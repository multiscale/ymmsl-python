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
        repeater_conduits: list[Conduit] = []
        incoming_timelines: list[TimelineNode] = []
        for conduit in f_init_conduits:
            if any(filter.is_repeater() for filter in conduit.filters):
                repeater_conduits.append(conduit)
                continue
            timeline = self._timeline_for_sending_port(conduit.sender)
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

        # Check consistency of conduits with repeaters
        for conduit in repeater_conduits:
            timeline1 = self._timeline_for_sending_port(conduit.sender)
            timeline2 = determined_timeline
            for filter in conduit.filters:
                if timeline1 is determined_timeline:
                    # TODO: better error message
                    raise ValueError(
                        "repeater after reducer cannot be in same timeline"
                    )
                if filter.is_reducer():
                    if timeline1.parent is None:
                        # TODO: better error message
                        raise ValueError("Too many reducer filters")
                    timeline1 = timeline1.parent
                if filter.is_repeater():
                    if timeline2.parent is None:
                        # TODO: better error message
                        raise ValueError("Too many repeater filters")
                    timeline2 = timeline2.parent
            if timeline1 is not timeline2:
                # TODO: better error message
                raise ValueError("Inconsistent timelines")

        # Done: register timeline for component
        self._component_timeline[component.name] = determined_timeline
        determined_timeline.add(component)

    def _timeline_for_sending_port(self, port_name: Reference) -> "TimelineNode":
        """Determine the resulting timeline for a component that connects (with f_init)
        to the provided port name."""
        component = port_name[:-1]
        if len(component) == 0:
            # Connected to a model port
            model_port = port_name[-1]
            assert isinstance(model_port, Identifier)
            port = self._model.ports[model_port]
            if port.operator is Operator.F_INIT:
                return self.root
            else:
                raise NotImplementedError()  # FIXME?
        timeline = self._component_timeline[component]
        port = self._all_ports[port_name]
        if port.operator is Operator.O_F:
            return timeline
        assert port.operator is Operator.O_I
        subtimeline = port.timeline
        if len(port.timeline) == 0:
            # No explicit label attached to the timeline, so we take the component name
            subtimeline = Timeline(str(component))
        return timeline.get(subtimeline)

    def component_timeline(self, component: Reference) -> Timeline:
        """Get the determined timeline for a component in the model"""
        return self._component_timeline[component].name


class TimelineNode:
    """Node in the timeline tree.

    Corresponds to a single timeline in a yMMSL model, and keeps track of components
    that are in that timeline.
    """

    def __init__(self, timeline: Timeline, parent: "TimelineNode | None") -> None:
        """Initialize timeline node for a given timeline"""

        self.name: Timeline = timeline
        """Name of this timeline."""
        self._parent: TimelineNode | None = parent
        """Parent node of this node."""
        self._children: dict[Reference, TimelineNode] = {}
        """Child timeline nodes."""
        self._components: list[Component] = []
        """List of components that are part of this timeline."""

    @property
    def parent(self) -> "TimelineNode | None":
        """Parent timeline node, or None if this is the root timeline."""
        return self._parent

    def get(self, subtimeline: Timeline) -> "TimelineNode":
        """Get a sub-timeline of this timeline, creating a new one if required."""
        assert not subtimeline.absolute
        assert len(subtimeline) == 1
        child = self._children.get(subtimeline[0])
        if child is None:
            child = TimelineNode(self.name + subtimeline, self)
            self._children[subtimeline[0]] = child
        return child

    def add(self, component: Component) -> None:
        """Add component to this timeline."""
        self._components.append(component)

    def __repr__(self) -> str:
        return f"TimelineNode({self.name})"
