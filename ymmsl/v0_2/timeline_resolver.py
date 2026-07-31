from ymmsl.v0_2 import (
    Component,
    Conduit,
    Identifier,
    Model,
    Operator,
    Port,
    Reference,
    Timeline,
)

ROOT_TIMELINE = Timeline(":")


def resolve_timelines(model: Model) -> None:
    """Determine timelines for each component and their O_I and S ports in this model.

    This function updates the timeline attributes of the components and ports in the
    model. Raises any of below subclasses of :class:`ResolveTimelineException` when the
    model timelines are not consistent.

    Raises:
        CyclicDependency: When messages to an F_INIT port of a component depend in some
            way on the output of that component.
        TooManyReducerFilters: When a conduit filter is applied to messages in the root
            timeline.
        InconsistentTimelines: When a component's F_INIT ports are not all connected to
            the same timeline.
        ConduitTimelineError: When a conduit connects incompatible timelines.
    """
    checker = TimelineChecker(model)
    checker.check_consistent()

    # Update timeline attributes
    for component in model.components.values():
        component.timeline = checker.component_timeline(component.name)
        for port in component.ports.values():
            full_port_name = component.name + port.name
            timeline = checker.timeline_for_port(full_port_name)
            port.timeline = timeline.relative_to(component.timeline)


class ResolveTimelineException(RuntimeError):
    """Base class for exceptions raised while resolving timelines."""


class CyclicDependency(ResolveTimelineException):
    """Error raised when some models form a dependency cycle.

    Dependency cycles occur when messages to an F_INIT port of a component depend in
    some way on the output of that component.
    """

    def __init__(
        self, model: Model, cycle: list[Component], conduits: list[Conduit]
    ) -> None:
        self.model = model
        self.cycle = cycle
        self.conduits = conduits
        cycle_str = " -> ".join(str(conduit) for conduit in reversed(conduits))
        super().__init__(
            f"Detected a dependency cycle in model '{model.name}'. The component "
            f"'{cycle[0].name}' has an F_INIT port that depends on data produced by "
            f"one of its own O_F or O_I ports: {cycle_str}. You may have an error "
            "in the conduits or may need a different coupling scheme."
        )


class TooManyReducerFilters(ResolveTimelineException):
    """Error raised when a conduit has too many reducer filters applied.

    This error is raised when a reducer filter attempts to reduce a conduit that
    already sends on the root timeline. :class:`InconsistentTimelines` or
    :class:`ConduitTimelineError` may also be raised when too many reducer filters are
    applied if that doesn't reduce the timeline beyond the root timeline.
    """

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


class InconsistentTimelines(ResolveTimelineException):
    """Error raised when a component's F_INIT ports have inconsistent timelines.

    When a component has multiple F_INIT ports, each port should receive on the same
    timeline. Note that :class:`ConduitTimelineError` may be raised for conduits
    connected to F_INIT ports when they have a repeater filter.
    """

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
                f"- Port '{conduit.receiving_port()}' has timeline '{timeline}' "
                f"from {conduit}"
                for conduit, timeline in zip(conduits, timelines)
            )
        )
        super().__init__(msg)


class ConduitTimelineError(ResolveTimelineException):
    """Error raised for conduits that connect incompatible timelines."""

    def __init__(
        self,
        checker: "TimelineChecker",
        conduit: Conduit,
        timeline1: Timeline,
        timeline2: Timeline,
        hint: str = "",
    ) -> None:
        self.checker = checker
        model = checker._model
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
            f"{checker.format_timelines()}"
        )
        super().__init__(msg)


class TimelineChecker:
    """Checks timelines and nesting for a given yMMSL model"""

    def __init__(self, model: Model) -> None:
        self._model = model
        """yMMSL model that is checked."""

        self._component_timeline: dict[Reference, Timeline] = {
            Reference([]): ROOT_TIMELINE,  # Support model ports
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
            self._assign_component(component, [], [])

    def _f_init_conduits_for_component(self, component: Component) -> list[Conduit]:
        """Get conduits that are connected to an F_INIT port on the component"""
        result = []
        for port in component.ports.values():
            if port.operator is Operator.F_INIT:
                conduit = self._conduits_by_receiver.get(component.name + port.name)
                if conduit is not None:
                    result.append(conduit)
        return result

    def _assign_component(
        self, component: Component, seen: list[Component], seen_conduits: list[Conduit]
    ) -> None:
        """Recursive component assignment, uses "seen" list for cycle detection."""
        if component in seen:
            idx = seen.index(component)
            cycle = seen[idx:] + [component]
            raise CyclicDependency(self._model, cycle, seen_conduits[idx:])
        f_init_conduits = self._f_init_conduits_for_component(component)

        # Ensure we know the timelines of the components attached to our F_INIT
        seen.append(component)
        for conduit in f_init_conduits:
            sender = conduit.sending_component()
            if sender not in self._component_timeline:
                seen_conduits.append(conduit)
                self._assign_component(
                    self._model.components[sender], seen, seen_conduits
                )
                seen_conduits.pop()
        seen.pop()

        # Now we can determine our timeline
        incoming_timelines: list[Timeline] = []
        checked_conduits: list[Conduit] = []  # To provide better error messages
        for conduit in f_init_conduits:
            if any(filter.is_repeater() for filter in conduit.filters):
                continue  # We cannot use repeater filters to determine the timeline
            timeline = sender_timeline = self.timeline_for_port(conduit.sender)
            for filter in conduit.filters:
                assert filter.is_reducer()
                if timeline.parent is None:
                    raise TooManyReducerFilters(self._model, conduit, sender_timeline)
                timeline = timeline.parent
            incoming_timelines.append(timeline)
            checked_conduits.append(conduit)

        determined_timeline = ROOT_TIMELINE
        if incoming_timelines:
            determined_timeline = incoming_timelines[0]
        if not all(tl == determined_timeline for tl in incoming_timelines):
            raise InconsistentTimelines(
                self._model, component, checked_conduits, incoming_timelines
            )

        # Done: register timeline for component
        self._component_timeline[component.name] = determined_timeline

    def timeline_for_port(self, port_name: Reference) -> Timeline:
        """Determine the timeline for messages sent or received on the provided port
        name."""
        component = port_name[:-1]
        if len(component) == 0:
            # Connected to a model port
            model_port = port_name[-1]
            assert isinstance(model_port, Identifier)
            port = self._model.ports[model_port]
            return ROOT_TIMELINE + port.timeline
        timeline = self._component_timeline[component]
        port = self._all_ports[port_name]
        if port.operator in (Operator.O_F, Operator.F_INIT):
            return timeline
        subtimeline = port.timeline
        if len(port.timeline) == 0:
            # No explicit label attached to the timeline, so we take the component name
            subtimeline = Timeline(str(component))
        return timeline + subtimeline

    def component_timeline(self, component: Reference) -> Timeline:
        """Get the determined timeline for a component in the model"""
        return self._component_timeline[component]

    def check_consistent(self) -> None:
        """Check if the timelines are consistent.

        N.B. Certain inconsistencies prevent initialization. This method performs
        additional checks.
        """
        # Check that all conduits connect consistently
        for conduit in self._model.conduits:
            timeline1 = self.timeline_for_port(conduit.sender)
            timeline2 = self.timeline_for_port(conduit.receiver)

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
            f"- Component '{comp}' has timeline '{tl}'"
            for comp, tl in self._component_timeline.items()
            if len(comp) > 0  # Ony print actual components
        )
