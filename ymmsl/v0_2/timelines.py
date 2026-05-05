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


class CyclicDependency(RuntimeError):
    """Error raised when some models form a dependency cycle.

    Dependency cycles occur when messages to an F_INIT port of a component depend in
    some way on the output of that component.
    """

    def __init__(self, model: Model, cycle: list[Component]) -> None:
        self.model = model
        self.cycle = cycle
        msg = (
            f"Detected a dependency cycle in model '{model.name}': "
            + " -> ".join(str(component.name) for component in cycle)
        )
        super().__init__(msg)


class TooManyReducerFilters(RuntimeError):
    """Error raised when a conduit has too many reducer filters applied."""

    def __init__(
        self, model: Model, conduit: Conduit, sender_timeline: Timeline
    ) -> None:
        self.model = model
        self.conduit = conduit
        self.sender_timeline = sender_timeline
        num_reducers = sum(filter.is_reducer() for filter in conduit.filters)
        msg = (
            f"{conduit} in model '{model.name}' has too many reducer filters. The "
            f"sending port ({conduit.sender}) has timeline ({sender_timeline}) and "
            f"can only be reduced {len(sender_timeline)} times, but there are "
            f"{num_reducers} reducer filters."
        )
        super().__init__(msg)


class InconsistentTimelines(RuntimeError):
    """Error raised when a component's F_INIT ports have inconsistent timelines."""

    def __init__(
        self,
        model: Model,
        component: Component,
        conduits: list[Conduit],
        timelines: list[Timeline],
    ) -> None:
        self.model = model
        self.component = component
        self.conduits = conduits
        self.timelines = timelines
        msg = (
            f"Component '{component.name}' in model '{model.name}' has different "
            f"timelines for the following F_INIT ports:\n"
            + "\n".join(
                f"- Port '{conduit.receiving_port()}' has timeline '{timeline}'"
                for conduit, timeline in zip(conduits, timelines)
            )
        )
        super().__init__(msg)


class ConduitTimelineError(RuntimeError):
    """Error raised for conduits that connect incompatible timelines."""

    def __init__(
        self,
        tltree: "TimelineTree",
        conduit: Conduit,
        timeline1: Timeline,
        timeline2: Timeline,
        hint: str = "",
    ) -> None:
        self.tltree = tltree
        model = tltree._model
        self.conduit = conduit
        self.timeline1 = timeline1
        self.timeline2 = timeline2
        self.hint = hint
        msg = (
            f"{conduit} in model '{model.name}' has inconsistent timelines: it "
            f"connects timeline '{timeline1}' with timeline '{timeline2}', but this "
            f"does not match with the filters of the conduit.{hint} Note that this "
            "error may also be caused by missing timeline annotations for O_I and S "
            "ports, or because the sending or receiving component has incorrect "
            "F_INIT conduits. Determined timelines per component:\n"
            f"{tltree.format_timelines()}"
        )
        super().__init__(msg)


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
            idx = seen.index(component)
            cycle = seen[idx:] + [component]
            raise CyclicDependency(self._model, cycle)
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
        checked_conduits: list[Conduit] = []  # To provide better error messages
        for conduit in f_init_conduits:
            if any(filter.is_repeater() for filter in conduit.filters):
                continue  # We cannot use repeater filters to determine the timeline
            timeline = self.timeline_for_port(conduit.sender)
            sender_timeline = timeline.name
            for filter in conduit.filters:
                assert filter.is_reducer()
                if timeline.parent is None:
                    raise TooManyReducerFilters(self._model, conduit, sender_timeline)
                timeline = timeline.parent
            incoming_timelines.append(timeline)
            checked_conduits.append(conduit)

        determined_timeline = self.root
        if incoming_timelines:
            determined_timeline = incoming_timelines[0]
        if not all(tl is determined_timeline for tl in incoming_timelines):
            timelines = [tl.name for tl in incoming_timelines]
            raise InconsistentTimelines(
                self._model, component, checked_conduits, timelines
            )

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
                raise TooManyReducerFilters(self._model, conduit, timeline1)
            if len(timeline1) - num_reducers + num_repeaters != len(timeline2):
                remove_msg = ""
                if len(timeline1) - num_reducers + num_repeaters < len(timeline2):
                    add_filter = "repeater ('pad' or 'repeat')"
                    if num_reducers > 0:
                        remove_msg = "reducer ('last')"
                else:
                    add_filter = "reducer ('last')"
                    if num_repeaters > 0:
                        remove_msg = "repeater ('pad' or 'repeat')"
                if remove_msg:
                    remove_msg = f" or remove a {remove_msg} filter"
                hint = f" You may need to add a {add_filter} filter{remove_msg}."
                raise ConduitTimelineError(self, conduit, timeline1, timeline2, hint)

            # Check consistency
            common_idx = len(timeline1) - num_reducers
            for idx, (part1, part2) in enumerate(zip(timeline1, timeline2)):
                if idx < common_idx:
                    if part1 != part2:
                        raise ConduitTimelineError(self, conduit, timeline1, timeline2)
                else:
                    if part1 == part2:
                        hint = " You may need to remove a repeater and reducer filter."
                        raise ConduitTimelineError(
                            self, conduit, timeline1, timeline2, hint
                        )

    def format_timelines(self) -> str:
        """Create a formatted list of determined timelines per component."""
        return "\n".join(
            f"- Component '{comp}' has timeline '{tl.name}'"
            for comp, tl in self._component_timeline.items()
            if len(comp) > 0  # Ony print actual components
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
