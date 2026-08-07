"""
A dependency-free URDF model: parsing, joint metadata and forward kinematics.

The native [`dalaran.urdf.UrdfTree`][] knows how to *log* a URDF (geometry plus
static transforms), but it lives behind the compiled bindings and speaks in
Dalaran archetypes. The [`Robot`][dalaran.robot.Robot] handle needs something
smaller and more introspectable: the joint metadata (axis, origin, limits,
mimic) and the link hierarchy, as plain numpy.

That is what this module is. It parses URDF XML with the standard library, and
implements the URDF kinematics (including `<mimic>` joints and limit clamping)
with numpy only, so it can be unit-tested without a native build. It can also
adopt an already-parsed [`dalaran.urdf.UrdfTree`][] via
[`UrdfModel.from_urdf_tree`][dalaran.robot.urdf_model.UrdfModel.from_urdf_tree],
which is how [`Robot.load_urdf`][dalaran.robot.Robot.load_urdf] avoids parsing
the same file twice.

Units and conventions are URDF's, which are REP-103's: meters, radians,
right-handed frames, fixed-axis `(roll, pitch, yaw)` origins.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any
from xml.etree import ElementTree

import numpy as np
import numpy.typing as npt

from ._math import compose, euler_to_matrix, identity, make_matrix

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator, Mapping

__all__ = [
    "CONTINUOUS",
    "FIXED",
    "MOVING_JOINT_TYPES",
    "PRISMATIC",
    "REVOLUTE",
    "JointSpec",
    "MimicSpec",
    "UrdfModel",
    "axis_angle_to_matrix",
]

REVOLUTE = "revolute"
"""A hinge joint with limits, driven in radians."""

CONTINUOUS = "continuous"
"""A hinge joint without limits, driven in radians."""

PRISMATIC = "prismatic"
"""A sliding joint with limits, driven in meters."""

FIXED = "fixed"
"""A rigid attachment; its value is ignored."""

MOVING_JOINT_TYPES: frozenset[str] = frozenset({REVOLUTE, CONTINUOUS, PRISMATIC})
"""The URDF joint types that a joint-state message can actually move."""


def axis_angle_to_matrix(axis: npt.ArrayLike, angle: float) -> npt.NDArray[np.float64]:
    """
    Rodrigues' rotation formula: rotate by `angle` radians about a unit `axis`.

    Examples
    --------
    ```python
    import numpy as np
    from dalaran.robot.urdf_model import axis_angle_to_matrix

    r = axis_angle_to_matrix([0.0, 0.0, 1.0], np.pi / 2)
    np.testing.assert_allclose(r @ [1, 0, 0], [0, 1, 0], atol=1e-12)
    ```

    """
    x, y, z = np.asarray(axis, dtype=np.float64).reshape(3)
    k = np.array([[0.0, -z, y], [z, 0.0, -x], [-y, x, 0.0]], dtype=np.float64)
    return np.eye(3) + np.sin(angle) * k + (1.0 - np.cos(angle)) * (k @ k)


def _unit(axis: npt.ArrayLike, *, what: str) -> npt.NDArray[np.float64]:
    arr = np.asarray(axis, dtype=np.float64).reshape(3)
    norm = float(np.linalg.norm(arr))
    if norm < 1e-12:
        msg = f"{what} has a zero-length axis"
        raise ValueError(msg)
    return arr / norm


@dataclass(frozen=True)
class MimicSpec:
    """
    A URDF `<mimic>` tag: this joint follows `multiplier * driver + offset`.

    Examples
    --------
    ```python
    from dalaran.robot.urdf_model import MimicSpec

    spec = MimicSpec(joint="left_finger", multiplier=-1.0)
    assert spec.apply(0.4) == -0.4
    ```

    """

    joint: str
    """Name of the driver joint."""

    multiplier: float = 1.0
    """Factor applied to the driver joint's value."""

    offset: float = 0.0
    """Constant added after multiplying the driver joint's value."""

    def apply(self, driver_value: float) -> float:
        """Return this joint's value for a given `driver_value`."""
        return self.multiplier * float(driver_value) + self.offset


@dataclass(frozen=True)
class JointSpec:
    """
    Everything [`Robot`][dalaran.robot.Robot] needs to know about one URDF joint.

    Examples
    --------
    ```python
    import numpy as np
    from dalaran.robot.urdf_model import JointSpec

    joint = JointSpec(
        name="shoulder",
        joint_type="revolute",
        parent_link="base_link",
        child_link="upper_arm",
        origin_xyz=(0.0, 0.0, 0.2),
        limit_lower=-1.0,
        limit_upper=1.0,
    )
    # The limits are honoured, and the origin offset is preserved.
    np.testing.assert_allclose(joint.transform(5.0)[:3, 3], [0.0, 0.0, 0.2])
    assert joint.clamp(5.0) == 1.0
    ```

    """

    name: str
    """The joint name, as it appears in `sensor_msgs/JointState` messages."""

    joint_type: str
    """One of `revolute`, `continuous`, `prismatic`, `fixed`, `floating` or `planar`."""

    parent_link: str
    """Name of the parent link."""

    child_link: str
    """Name of the child link."""

    axis: tuple[float, float, float] = (1.0, 0.0, 0.0)
    """The joint axis in the child frame; URDF's default is `+X`."""

    origin_xyz: tuple[float, float, float] = (0.0, 0.0, 0.0)
    """Translation of the joint frame relative to the parent link, in meters."""

    origin_rpy: tuple[float, float, float] = (0.0, 0.0, 0.0)
    """Fixed-axis `(roll, pitch, yaw)` of the joint frame, in radians."""

    limit_lower: float | None = None
    """Lower position limit, or `None` when the joint is unlimited."""

    limit_upper: float | None = None
    """Upper position limit, or `None` when the joint is unlimited."""

    limit_effort: float | None = None
    """Effort limit, purely informational here."""

    limit_velocity: float | None = None
    """Velocity limit, purely informational here."""

    mimic: MimicSpec | None = None
    """The `<mimic>` specification, or `None` for an independently driven joint."""

    @property
    def is_moving(self) -> bool:
        """Whether a joint value can move this joint at all."""
        return self.joint_type in MOVING_JOINT_TYPES

    @property
    def is_actuated(self) -> bool:
        """Whether this joint is moving *and* driven directly rather than by a mimic tag."""
        return self.is_moving and self.mimic is None

    @property
    def unit(self) -> str:
        """`"rad"` for hinge joints, `"m"` for prismatic ones, `""` for fixed ones."""
        if self.joint_type in (REVOLUTE, CONTINUOUS):
            return "rad"
        if self.joint_type == PRISMATIC:
            return "m"
        return ""

    def origin_matrix(self) -> npt.NDArray[np.float64]:
        """Return the 4x4 `parent_from_child` transform at joint value zero."""
        return make_matrix(translation=self.origin_xyz, rotation=euler_to_matrix(self.origin_rpy))

    def clamp(self, value: float) -> float:
        """
        Clamp `value` into this joint's limits.

        Continuous and fixed joints, and joints without a `<limit>` tag, are
        returned untouched: URDF only requires limits on revolute and prismatic
        joints, and clamping a continuous joint would be wrong.
        """
        out = float(value)
        if self.joint_type == CONTINUOUS or not self.is_moving:
            return out
        if self.limit_lower is not None:
            out = max(out, self.limit_lower)
        if self.limit_upper is not None:
            out = min(out, self.limit_upper)
        return out

    def transform(self, value: float, *, clamp: bool = True) -> npt.NDArray[np.float64]:
        """
        Return the 4x4 `parent_from_child` transform of this joint at `value`.

        Parameters
        ----------
        value:
            Radians for `revolute`/`continuous`, meters for `prismatic`, ignored
            for every other type.
        clamp:
            Whether to clamp `value` into the joint limits first.

        """
        if not self.is_moving:
            return self.origin_matrix()
        position = self.clamp(value) if clamp else float(value)
        axis = _unit(self.axis, what=f"Joint {self.name!r}")
        if self.joint_type == PRISMATIC:
            motion = make_matrix(translation=axis * position)
        else:
            motion = make_matrix(rotation=axis_angle_to_matrix(axis, position))
        return compose(self.origin_matrix(), motion)


def _floats(text: str | None, default: tuple[float, float, float]) -> tuple[float, float, float]:
    if text is None:
        return default
    parts = [float(p) for p in text.replace(",", " ").split()]
    if len(parts) != 3:
        msg = f"Expected 3 numbers, got {text!r}"
        raise ValueError(msg)
    return (parts[0], parts[1], parts[2])


def _optional_float(value: str | None) -> float | None:
    return None if value is None else float(value)


def _joint_from_xml(element: ElementTree.Element) -> JointSpec:
    name = element.get("name")
    joint_type = element.get("type")
    if not name or not joint_type:
        msg = "Every <joint> needs a `name` and a `type`"
        raise ValueError(msg)

    parent = element.find("parent")
    child = element.find("child")
    if parent is None or child is None:
        msg = f"Joint {name!r} is missing a <parent> or <child> link"
        raise ValueError(msg)
    parent_link = parent.get("link")
    child_link = child.get("link")
    if not parent_link or not child_link:
        msg = f"Joint {name!r} has a <parent>/<child> without a `link` attribute"
        raise ValueError(msg)

    origin = element.find("origin")
    axis_element = element.find("axis")
    limit = element.find("limit")
    mimic_element = element.find("mimic")

    mimic: MimicSpec | None = None
    if mimic_element is not None:
        driver = mimic_element.get("joint")
        if not driver:
            msg = f"Joint {name!r} has a <mimic> tag without a `joint` attribute"
            raise ValueError(msg)
        mimic = MimicSpec(
            joint=driver,
            multiplier=float(mimic_element.get("multiplier", 1.0)),
            offset=float(mimic_element.get("offset", 0.0)),
        )

    return JointSpec(
        name=name,
        joint_type=joint_type,
        parent_link=parent_link,
        child_link=child_link,
        axis=_floats(None if axis_element is None else axis_element.get("xyz"), (1.0, 0.0, 0.0)),
        origin_xyz=_floats(None if origin is None else origin.get("xyz"), (0.0, 0.0, 0.0)),
        origin_rpy=_floats(None if origin is None else origin.get("rpy"), (0.0, 0.0, 0.0)),
        limit_lower=None if limit is None else _optional_float(limit.get("lower")),
        limit_upper=None if limit is None else _optional_float(limit.get("upper")),
        limit_effort=None if limit is None else _optional_float(limit.get("effort")),
        limit_velocity=None if limit is None else _optional_float(limit.get("velocity")),
        mimic=mimic,
    )


@dataclass
class UrdfModel:
    """
    A parsed URDF: its links, its joints, and the kinematics that connect them.

    Parameters
    ----------
    name:
        The robot name from the URDF's `<robot name=...>` attribute.
    links:
        Link names, in document order.
    joints:
        The joints, in document order.

    Examples
    --------
    ```python
    from dalaran.robot.urdf_model import UrdfModel

    xml = (
        '<robot name="arm">'
        '  <link name="base_link"/>'
        '  <link name="upper_arm"/>'
        '  <joint name="shoulder" type="revolute">'
        '    <parent link="base_link"/>'
        '    <child link="upper_arm"/>'
        '    <axis xyz="0 0 1"/>'
        '    <limit lower="-1.0" upper="1.0"/>'
        '  </joint>'
        '</robot>'
    )
    model = UrdfModel.from_string(xml)
    assert model.root_link == "base_link"
    assert model.actuated_joint_names == ["shoulder"]
    ```

    """

    name: str
    links: list[str]
    joints: list[JointSpec]
    _joints_by_name: dict[str, JointSpec] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._joints_by_name = {}
        for joint in self.joints:
            if joint.name in self._joints_by_name:
                msg = f"Duplicate joint name {joint.name!r} in URDF {self.name!r}"
                raise ValueError(msg)
            self._joints_by_name[joint.name] = joint

        known = set(self.links)
        for joint in self.joints:
            for link in (joint.parent_link, joint.child_link):
                if link not in known:
                    self.links.append(link)
                    known.add(link)

        for joint in self.joints:
            if joint.mimic is not None and joint.mimic.joint not in self._joints_by_name:
                msg = f"Joint {joint.name!r} mimics unknown joint {joint.mimic.joint!r}"
                raise ValueError(msg)

    # -- construction ------------------------------------------------------

    @staticmethod
    def from_string(xml: str) -> UrdfModel:
        """Parse a URDF from an XML string."""
        root = ElementTree.fromstring(xml)  # noqa: S314 - URDFs are local robot descriptions
        if root.tag != "robot":
            msg = f"Expected a <robot> root element, got <{root.tag}>"
            raise ValueError(msg)
        return UrdfModel(
            name=root.get("name", "robot"),
            links=[link.get("name", "") for link in root.findall("link")],
            joints=[_joint_from_xml(joint) for joint in root.findall("joint")],
        )

    @staticmethod
    def from_file(path: str | Path) -> UrdfModel:
        """Parse a URDF from a file on disk."""
        return UrdfModel.from_string(Path(path).read_text(encoding="utf-8"))

    @staticmethod
    def from_urdf_tree(tree: Any) -> UrdfModel:
        """
        Adopt an already-parsed [`dalaran.urdf.UrdfTree`][].

        Only the duck-typed surface (`name`, `joints()`, `root_link()`) is used,
        so a stand-in object works just as well as the native tree - which is
        what the unit tests rely on.
        """
        joints = [
            JointSpec(
                name=joint.name,
                joint_type=joint.joint_type,
                parent_link=joint.parent_link,
                child_link=joint.child_link,
                axis=tuple(joint.axis),  # type: ignore[arg-type]
                origin_xyz=tuple(joint.origin_xyz),  # type: ignore[arg-type]
                origin_rpy=tuple(joint.origin_rpy),  # type: ignore[arg-type]
                limit_lower=_limit(joint, "limit_lower"),
                limit_upper=_limit(joint, "limit_upper"),
                limit_effort=_limit(joint, "limit_effort"),
                limit_velocity=_limit(joint, "limit_velocity"),
                mimic=(
                    None
                    if joint.mimic is None
                    else MimicSpec(
                        joint=joint.mimic.joint,
                        multiplier=float(joint.mimic.multiplier),
                        offset=float(joint.mimic.offset),
                    )
                ),
            )
            for joint in tree.joints()
        ]
        links = [tree.root_link().name]
        links += [joint.child_link for joint in joints]
        return UrdfModel(name=getattr(tree, "name", "robot"), links=links, joints=joints)

    # -- structure ---------------------------------------------------------

    @property
    def joint_names(self) -> list[str]:
        """All joint names, in document order."""
        return [joint.name for joint in self.joints]

    @property
    def actuated_joint_names(self) -> list[str]:
        """Names of joints that a joint-state message drives directly (no mimics, no fixed joints)."""
        return [joint.name for joint in self.joints if joint.is_actuated]

    @property
    def mimic_joint_names(self) -> list[str]:
        """Names of joints whose value is derived from another joint."""
        return [joint.name for joint in self.joints if joint.mimic is not None]

    @property
    def root_link(self) -> str:
        """
        The link that is not the child of any joint.

        Raises
        ------
        ValueError
            If the URDF has no root link, or more than one (a disconnected model).

        """
        children = {joint.child_link for joint in self.joints}
        roots = [link for link in self.links if link not in children]
        if not roots:
            msg = f"URDF {self.name!r} has no root link; the link graph contains a cycle"
            raise ValueError(msg)
        if len(roots) > 1:
            msg = f"URDF {self.name!r} is disconnected; candidate root links are {roots}"
            raise ValueError(msg)
        return roots[0]

    def joint(self, name: str) -> JointSpec:
        """Return the joint called `name`, raising `KeyError` if it does not exist."""
        try:
            return self._joints_by_name[name]
        except KeyError:
            msg = f"Unknown joint {name!r}; this URDF declares {sorted(self._joints_by_name)}"
            raise KeyError(msg) from None

    def __contains__(self, joint_name: str) -> bool:
        return joint_name in self._joints_by_name

    def joint_for_child_link(self, link: str) -> JointSpec | None:
        """Return the joint whose child is `link`, or `None` for the root link."""
        for joint in self.joints:
            if joint.child_link == link:
                return joint
        return None

    def iter_joints_parents_first(self) -> Iterator[JointSpec]:
        """
        Yield joints so that a joint's parent link is always known before its child.

        This is the order in which frames must be declared in a
        [`TransformTree`][dalaran.robot.TransformTree].
        """
        pending = list(self.joints)
        available = {self.root_link}
        while pending:
            progressed = False
            still_pending: list[JointSpec] = []
            for joint in pending:
                if joint.parent_link in available:
                    available.add(joint.child_link)
                    progressed = True
                    yield joint
                else:
                    still_pending.append(joint)
            if not progressed:
                names = [joint.name for joint in still_pending]
                msg = f"URDF {self.name!r} contains a kinematic cycle involving {names}"
                raise ValueError(msg)
            pending = still_pending

    # -- kinematics --------------------------------------------------------

    def resolve_positions(
        self,
        positions: Mapping[str, float],
        *,
        clamp: bool = True,
    ) -> dict[str, float]:
        """
        Expand a set of driven joint values into every joint value they imply.

        Mimic joints are resolved (transitively, so a mimic of a mimic works),
        and every value is clamped into its joint limits unless `clamp=False`.
        Unknown joint names are ignored here; the caller is better placed to
        report them.

        Parameters
        ----------
        positions:
            Joint values keyed by joint name.
        clamp:
            Whether to clamp values into the joint limits.

        Returns
        -------
        dict
            Every joint value implied by `positions`, keyed by joint name.

        Examples
        --------
        ```python
        from dalaran.robot.urdf_model import JointSpec, MimicSpec, UrdfModel

        model = UrdfModel(
            name="gripper",
            links=["palm", "left", "right"],
            joints=[
                JointSpec("left_finger", "prismatic", "palm", "left", limit_lower=0.0, limit_upper=0.04),
                JointSpec(
                    "right_finger",
                    "prismatic",
                    "palm",
                    "right",
                    mimic=MimicSpec("left_finger", multiplier=-1.0),
                ),
            ],
        )
        resolved = model.resolve_positions({"left_finger": 0.03})
        assert resolved["right_finger"] == -0.03
        ```

        """
        resolved: dict[str, float] = {}
        for name, value in positions.items():
            joint = self._joints_by_name.get(name)
            if joint is None:
                continue
            resolved[name] = joint.clamp(value) if clamp else float(value)

        # Mimic joints may chain, so iterate to a fixed point. The number of
        # joints bounds the longest possible chain.
        for _ in range(len(self.joints)):
            changed = False
            for joint in self.joints:
                if joint.mimic is None or joint.name in resolved:
                    continue
                driver = resolved.get(joint.mimic.joint)
                if driver is None:
                    continue
                value = joint.mimic.apply(driver)
                resolved[joint.name] = joint.clamp(value) if clamp else value
                changed = True
            if not changed:
                break
        return resolved

    def joint_transforms(
        self,
        positions: Mapping[str, float],
        *,
        clamp: bool = True,
        resolve_mimics: bool = True,
    ) -> dict[str, npt.NDArray[np.float64]]:
        """
        Return the `parent_from_child` transform of every joint, as 4x4 matrices.

        Joints missing from `positions` are evaluated at zero, which is what a
        partial `sensor_msgs/JointState` message means in practice.
        """
        values = self.resolve_positions(positions, clamp=clamp) if resolve_mimics else dict(positions)
        return {joint.name: joint.transform(values.get(joint.name, 0.0), clamp=clamp) for joint in self.joints}

    def link_transforms(
        self,
        positions: Mapping[str, float],
        *,
        clamp: bool = True,
    ) -> dict[str, npt.NDArray[np.float64]]:
        """
        Forward kinematics: every link's pose relative to the root link.

        Parameters
        ----------
        positions:
            Joint values keyed by joint name; missing joints are held at zero.
        clamp:
            Whether to clamp values into the joint limits.

        Returns
        -------
        dict
            `root_from_link` 4x4 matrices, keyed by link name.

        Examples
        --------
        ```python
        import numpy as np
        from dalaran.robot.urdf_model import JointSpec, UrdfModel

        model = UrdfModel(
            name="arm",
            links=["base_link", "upper_arm"],
            joints=[JointSpec("shoulder", "prismatic", "base_link", "upper_arm", axis=(0.0, 0.0, 1.0))],
        )
        poses = model.link_transforms({"shoulder": 0.5})
        np.testing.assert_allclose(poses["upper_arm"][:3, 3], [0.0, 0.0, 0.5])
        ```

        """
        local = self.joint_transforms(positions, clamp=clamp)
        poses: dict[str, npt.NDArray[np.float64]] = {self.root_link: identity()}
        for joint in self.iter_joints_parents_first():
            poses[joint.child_link] = compose(poses[joint.parent_link], local[joint.name])
        return poses

    def unknown_joints(self, names: Iterable[str]) -> list[str]:
        """Return the subset of `names` this URDF does not declare, in input order."""
        return [name for name in names if name not in self._joints_by_name]

    def check_limits(self, positions: Mapping[str, float], *, warn: bool = True) -> dict[str, float]:
        """
        Return the joint values that had to be clamped, optionally warning about them.

        The returned mapping keys are joint names and the values are the
        *original* out-of-limit values, which is what you want in an error
        message.
        """
        violations: dict[str, float] = {}
        for name, value in positions.items():
            joint = self._joints_by_name.get(name)
            if joint is None:
                continue
            if joint.clamp(value) != float(value):
                violations[name] = float(value)
        if warn and violations:
            details = ", ".join(f"{name}={value:g}" for name, value in sorted(violations.items()))
            warnings.warn(
                f"Clamped out-of-limit joint values in URDF {self.name!r}: {details}",
                UserWarning,
                stacklevel=2,
            )
        return violations

    def __repr__(self) -> str:
        return f"UrdfModel(name={self.name!r}, links={len(self.links)}, joints={len(self.joints)})"


def _limit(joint: Any, attribute: str) -> float | None:
    """Read a limit off a native `UrdfJoint`, mapping its non-finite sentinels to `None`."""
    value = getattr(joint, attribute, None)
    if value is None:
        return None
    value = float(value)
    return None if not np.isfinite(value) else value
