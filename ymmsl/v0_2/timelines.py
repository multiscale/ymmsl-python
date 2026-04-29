from typing import Optional
from ymmsl.v0_2 import (
    Component,
    Conduit,
    Model,
    Operator,
    Port,
    Reference,
    Timeline,
    Identifier,
)


class TimelineTree:
    """Determines timelines and nesting for a given yMMSL model"""

    def __init__(self, model: Model) -> None:
        self._model = model
        """yMMSL model that this TimelineTree belongs to."""
        self.root = TimelineNode(Timeline(":"), None)
        """Timeline node of the root timeline."""

        self._component_timeline: dict[Reference, TimelineNode] = {
            Reference([]): self.root,  # Support model ports
        }
        """Map of component names to the TimelineNode they are part of."""
        self._conduits_by_receiver: dict[Reference, Conduit] = {
            conduit.receiver: conduit for conduit in self._model.conduits
        }
        """Map of conduits by their receiving port"""
        self._all_ports: dict[Reference, Port] = {
            component.name + port_name: port
            for component in self._model.components.values()
            for port_name, port in component.ports.items()
        }
        """Map of Port objects by their full reference"""

        # Assign components to timelines
        for component in self._model.components.values():
            if component.name in self._component_timeline:
                continue
            self._assign_component(component, [])

    def _f_init_conduits_for_component(self, component: Component) -> list[Conduit]:
        """Get conduits that are connected to an F_INIT port on the component"""
        result = []
        for port in component.ports.values():
            if port.operator is Operator.F_INIT:
                conduit = self._conduits_by_receiver.get(component.name + port.name)
                if conduit is not None:
                    result.append(conduit)
        return result

    def _assign_component(self, component: Component, seen: list[Component]) -> None:
        """Recursive component assignment, uses "seen" list for cycle detection."""
        if component in seen:
            # TODO: better error message
            idx = seen.index(component)
            cycle_list = seen[idx:] + [component]
            cycle = " -> ".join(str(component.name) for component in cycle_list)
            raise RuntimeError(f"Cycle detected in model '{self._model.name}': {cycle}")
        f_init_conduits = self._f_init_conduits_for_component(component)

        # Ensure we know the timelines of the components attached to our F_INIT
        seen.append(component)
        for conduit in f_init_conduits:
            sender = conduit.sending_component()
            if sender not in self._component_timeline:
                self._assign_component(self._model.components[sender], seen)
        seen.pop()

        # Now we can determine our timeline
        incoming_timelines: list[TimelineNode] = []
        for conduit in f_init_conduits:
            if any(filter.is_repeater() for filter in conduit.filters):
                continue  # We cannot use repeater filters to determine the timeline
            timeline = self.timeline_for_port(conduit.sender)
            for filter in conduit.filters:
                assert filter.is_reducer()
                if timeline.parent is None:
                    # TODO: better error message
                    raise ValueError("Too many reducer filters")
                timeline = timeline.parent
            incoming_timelines.append(timeline)

        determined_timeline = self.root
        if incoming_timelines:
            determined_timeline = incoming_timelines[0]
        if not all(tl is determined_timeline for tl in incoming_timelines):
            # TODO: better error message
            raise ValueError(f"Inconsistent timelines {incoming_timelines}")

        # Done: register timeline for component
        self._component_timeline[component.name] = determined_timeline
        determined_timeline._add(component)
        self._assign_subtimelines(component)

    def _assign_subtimelines(self, component: Component) -> None:
        """Assign subtimelines to this component (and create them as necessary)."""
        for port in component.ports.values():
            if port.operator in (Operator.O_I, Operator.S):
                subtimeline = self.timeline_for_port(component.name + port.name)
                subtimeline._add_parent(component)

    def timeline_for_port(self, port_name: Reference) -> "TimelineNode":
        """Determine the timeline for messages sent or received on the provided port
        name."""
        component = port_name[:-1]
        if len(component) == 0:
            # Connected to a model port
            model_port = port_name[-1]
            assert isinstance(model_port, Identifier)
            port = self._model.ports[model_port]
            return self.root._get(port.timeline)
        timeline = self._component_timeline[component]
        port = self._all_ports[port_name]
        if port.operator in (Operator.O_F, Operator.F_INIT):
            return timeline
        subtimeline = port.timeline
        if len(port.timeline) == 0:
            # No explicit label attached to the timeline, so we take the component name
            subtimeline = Timeline(str(component))
        return timeline._get(subtimeline)

    def component_timeline(self, component: Reference) -> Timeline:
        """Get the determined timeline for a component in the model"""
        return self._component_timeline[component].name

    def check_consistent(self) -> None:
        """Check if the timelines are consistent.

        N.B. Certain inconsistencies prevent creating a TimelineTree at all. This method
        performs additional checks.
        """
        # Check that all conduits connect consistently
        for conduit in self._model.conduits:
            timeline1 = self.timeline_for_port(conduit.sender).name
            timeline2 = self.timeline_for_port(conduit.receiver).name

            num_reducers = sum(filter.is_reducer() for filter in conduit.filters)
            num_repeaters = sum(filter.is_repeater() for filter in conduit.filters)
            num_filters = len(conduit.filters)
            assert num_reducers + num_repeaters == num_filters

            # Apply reducers
            if len(timeline1) < num_reducers:
                # TODO: better error message
                raise ValueError("Too many reducer filters")
            if len(timeline1) - num_reducers + num_repeaters != len(timeline2):
                # TODO: better error message
                raise ValueError("Inconsistent conduit filters")

            # Check consistency
            common_idx = len(timeline1) - num_reducers
            for idx, (part1, part2) in enumerate(zip(timeline1, timeline2)):
                if idx < common_idx:
                    if part1 != part2:
                        # TODO: better error message
                        raise ValueError("Inconsistent timelines")
                else:
                    if part1 == part2:
                        # TODO: better error message
                        raise ValueError(
                            "repeater after reducer cannot be in same timeline"
                        )


class TimelineNode:
    """Node in the timeline tree.

    Corresponds to a single timeline in a yMMSL model, and keeps track of components
    that are in that timeline.
    """

    def __init__(self, timeline: Timeline, parent: "TimelineNode | None") -> None:
        """Initialize timeline node for a given timeline"""

        self.name: Timeline = timeline
        """Name of this timeline."""
        self._parent: Optional[TimelineNode] = parent
        """Parent node of this node."""
        self._parent_components: list[Component] = []
        """Parent components, i.e. components with O_I or S ports that send messages in
        this timeline."""
        self._children: dict[Reference, TimelineNode] = {}
        """Child timeline nodes."""
        self._components: list[Component] = []
        """List of components that are part of this timeline."""

    @property
    def parent(self) -> "TimelineNode | None":
        """Parent timeline node, or None if this is the root timeline."""
        return self._parent

    @property
    def parent_components(self) -> list[Component]:
        """List of all components that have an O_I or S port sending or receiving
        messages in this subtimeline."""
        return self._parent_components.copy()

    @property
    def children(self) -> list["TimelineNode"]:
        """List of all sub-timelines of this one."""
        return list(self._children.values())

    @property
    def components(self) -> list[Component]:
        """List of all components that are part of this timeline."""
        return self._components.copy()

    def _get(self, subtimeline: Timeline) -> "TimelineNode":
        """Get a sub-timeline of this timeline, creating a new one if required."""
        assert not subtimeline.absolute
        node = self
        for part in subtimeline:
            child = node._children.get(part)
            if child is None:
                child = TimelineNode(node.name + Timeline([part], False), node)
                node._children[part] = child
            node = child
        return node

    def _add(self, component: Component) -> None:
        """Add component to this timeline."""
        self._components.append(component)

    def _add_parent(self, component: Component) -> None:
        """Add parent component to this timeline."""
        if component not in self._parent_components:
            self._parent_components.append(component)

    def __repr__(self) -> str:
        return f"TimelineNode({self.name})"
