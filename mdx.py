from abc import abstractmethod
from typing import List, Optional

from ordered_set import OrderedSet

ELEMENT_ATTRIBUTE_PREFIX = "}ELEMENTATTRIBUTES_"


def normalize(name: str) -> str:
    return name.upper().replace(" ", "").replace("]", "]]")


class Member:

    def __init__(self, dimension: str, hierarchy: str, element: str):
        self.dimension = dimension
        self.hierarchy = hierarchy
        self.element = element
        self.unique_name = self.build_unique_name(dimension, hierarchy, element)

    @classmethod
    def build_unique_name(cls, dimension, hierarchy, element) -> str:
        return f"[{normalize(dimension)}].[{normalize(hierarchy)}].[{normalize(element)}]"

    @staticmethod
    def of(*args: str) -> 'Member':
        if len(args) == 2:
            return Member(args[0], args[0], args[1])
        elif len(args) == 3:
            return Member(*args)
        else:
            raise ValueError("method takes either two or three arguments")

    def __eq__(self, other) -> bool:
        return self.unique_name == other.unique_name

    def __hash__(self):
        return hash(self.unique_name)


class MdxTuple:

    def __init__(self, members):
        self.members = OrderedSet(members)

    @staticmethod
    def of(*args: Member) -> 'MdxTuple':
        mdx_tuple = MdxTuple(args)
        return mdx_tuple

    @staticmethod
    def empty() -> 'MdxTuple':
        return MdxTuple.of()

    def add_member(self, member: Member):
        self.members.add(member)

    def is_empty(self) -> bool:
        return len(self.members) == 0

    def to_mdx(self) -> str:
        return f"({','.join(member.unique_name for member in self.members)})"

    def __len__(self):
        return len(self.members)


class MdxHierarchySet:

    def __init__(self, dimension: str, hierarchy: Optional[str] = None):
        self.dimension = normalize(dimension)
        self.hierarchy = normalize(hierarchy) if hierarchy else self.dimension

    @abstractmethod
    def to_mdx(self) -> str:
        pass

    @staticmethod
    def tm1_subset_all(dimension: str, hierarchy: str = None) -> 'MdxHierarchySet':
        return Tm1SubsetAllHierarchySet(dimension, hierarchy)

    @staticmethod
    def all_members(dimension: str, hierarchy: str) -> 'MdxHierarchySet':
        return AllMembersHierarchySet(dimension, hierarchy)

    @staticmethod
    def tm1_subset_to_set(dimension: str, hierarchy: str, subset: str) -> 'MdxHierarchySet':
        return Tm1SubsetToSetHierarchySet(dimension, hierarchy, subset)

    @staticmethod
    def all_consolidations(dimension: str, hierarchy: str = None) -> 'MdxHierarchySet':
        return AllCElementsHierarchySet(dimension, hierarchy)

    @staticmethod
    def all_leaves(dimension: str, hierarchy: str = None) -> 'MdxHierarchySet':
        return AllLeafElementsHierarchySet(dimension, hierarchy)

    @staticmethod
    def default_member(dimension: str, hierarchy: str = None) -> 'MdxHierarchySet':
        return DefaultMemberHierarchySet(dimension, hierarchy)

    @staticmethod
    def member(member: Member) -> 'MdxHierarchySet':
        return ElementsHierarchySet(member)

    @staticmethod
    def members(members: List[Member]) -> 'MdxHierarchySet':
        return ElementsHierarchySet(*members)

    @staticmethod
    def parent(member: Member) -> 'MdxHierarchySet':
        return ParentHierarchySet(member)

    @staticmethod
    def first_child(member: Member) -> 'MdxHierarchySet':
        return FirstChildHierarchySet(member)

    @staticmethod
    def last_child(member: Member) -> 'MdxHierarchySet':
        return LastChildHierarchySet(member)

    @staticmethod
    def children(member: Member) -> 'MdxHierarchySet':
        return ChildrenHierarchySet(member)

    @staticmethod
    def ancestors(member: Member) -> 'MdxHierarchySet':
        return AncestorsHierarchySet(member)

    @staticmethod
    def ancestor(member: Member, ancestor: int) -> 'MdxHierarchySet':
        return AncestorHierarchySet(member, ancestor)

    @staticmethod
    def drill_down_level(member: Member) -> 'MdxHierarchySet':
        return DrillDownLevelHierarchySet(member)

    @staticmethod
    def descendants(member: Member) -> 'MdxHierarchySet':
        return DescendantsHierarchySet(member)

    def filter_by_attribute(self, attribute_name: str, attribute_values: List) -> 'MdxHierarchySet':
        return FilterByAttributeHierarchySet(self, attribute_name, attribute_values)

    def filter_by_pattern(self, wildcard: str) -> 'MdxHierarchySet':
        return Tm1FilterByPattern(self, wildcard)

    def filter_by_level(self, level: int) -> 'MdxHierarchySet':
        return Tm1FilterByLevelHierarchySet(self, level)

    def filter_by_cell_value(self, cube: str, mdx_tuple: MdxTuple, operator: str, value) -> 'MdxHierarchySet':
        return FilterByCellValueHierarchySet(self, cube, mdx_tuple, operator, value)

    def tm1_sort(self, ascending=True) -> 'MdxHierarchySet':
        return Tm1SortHierarchySet(self, ascending)

    def head(self, head: int) -> 'MdxHierarchySet':
        return HeadHierarchySet(self, head)

    def tail(self, tail: int) -> 'MdxHierarchySet':
        return TailHierarchySet(self, tail)

    def subset(self, start: int, length: int) -> 'MdxHierarchySet':
        return SubsetHierarchySet(self, start, length)

    def top_count(self, cube, mdx_tuple, top) -> 'MdxHierarchySet':
        return TopCountHierarchySet(self, cube, mdx_tuple, top)

    def bottom_count(self, cube, mdx_tuple, top) -> 'MdxHierarchySet':
        return BottomCountHierarchySet(self, cube, mdx_tuple, top)

    def union(self, other_set: 'MdxHierarchySet') -> 'MdxHierarchySet':
        return UnionHierarchySet(self, other_set)

    def intersect(self, other_set: 'MdxHierarchySet') -> 'MdxHierarchySet':
        return IntersectHierarchySet(self, other_set)

    # avoid conflict with reserved word `except`
    def except_(self, other_set: 'MdxHierarchySet') -> 'MdxHierarchySet':
        return ExceptHierarchySet(self, other_set)

    def order(self, cube, mdx_tuple) -> 'MdxHierarchySet':
        return OrderByCellValueHierarchySet(self, cube, mdx_tuple)


class Tm1SubsetAllHierarchySet(MdxHierarchySet):

    def __init__(self, dimension: str, hierarchy: str = None):
        super(Tm1SubsetAllHierarchySet, self).__init__(dimension, hierarchy)

    def to_mdx(self) -> str:
        return f"{{TM1SUBSETALL([{self.dimension}].[{self.hierarchy}])}}"


class AllMembersHierarchySet(MdxHierarchySet):

    def __init__(self, dimension: str, hierarchy: str = None):
        super(AllMembersHierarchySet, self).__init__(dimension, hierarchy)

    def to_mdx(self) -> str:
        return f"{{[{self.dimension}].[{self.hierarchy}].MEMBERS}}"


class AllCElementsHierarchySet(MdxHierarchySet):

    def __init__(self, dimension: str, hierarchy: str = None):
        super(AllCElementsHierarchySet, self).__init__(dimension, hierarchy)

    def to_mdx(self) -> str:
        return f"{{EXCEPT({{TM1SUBSETALL([{self.dimension}].[{self.hierarchy}])}}," \
               f"{{TM1FILTERBYLEVEL({{TM1SUBSETALL([{self.dimension}].[{self.hierarchy}])}},0)}})}}"


class AllLeafElementsHierarchySet(MdxHierarchySet):

    def __init__(self, dimension: str, hierarchy: str = None):
        super(AllLeafElementsHierarchySet, self).__init__(dimension, hierarchy)

    def to_mdx(self) -> str:
        return f"{{TM1FILTERBYLEVEL({{TM1SUBSETALL([{self.dimension}].[{self.hierarchy}])}},0)}}"


class DefaultMemberHierarchySet(MdxHierarchySet):

    def __init__(self, dimension: str, hierarchy: str = None):
        super(DefaultMemberHierarchySet, self).__init__(dimension, hierarchy)

    def to_mdx(self) -> str:
        return f"{{[{self.dimension}].[{self.hierarchy}].DEFAULTMEMBER}}"


class ElementsHierarchySet(MdxHierarchySet):

    def __init__(self, *members: Member):
        if not members:
            raise RuntimeError('members must not be empty')

        super(ElementsHierarchySet, self).__init__(members[0].dimension, members[0].hierarchy)
        self.members = members

    def to_mdx(self) -> str:
        return f"{{{','.join(member.unique_name for member in self.members)}}}"


class ParentHierarchySet(MdxHierarchySet):

    def __init__(self, member: Member):
        super(ParentHierarchySet, self).__init__(member.dimension, member.hierarchy)
        self.member = member

    def to_mdx(self) -> str:
        return f"{{{self.member.unique_name}.PARENT}}"


class FirstChildHierarchySet(MdxHierarchySet):

    def __init__(self, member: Member):
        super(FirstChildHierarchySet, self).__init__(member.dimension, member.hierarchy)
        self.member = member

    def to_mdx(self) -> str:
        return f"{{{self.member.unique_name}.FIRSTCHILD}}"


class LastChildHierarchySet(MdxHierarchySet):

    def __init__(self, member: Member):
        super(LastChildHierarchySet, self).__init__(member.dimension, member.hierarchy)
        self.member = member

    def to_mdx(self) -> str:
        return f"{{{self.member.unique_name}.LASTCHILD}}"


class AncestorsHierarchySet(MdxHierarchySet):

    def __init__(self, member: Member):
        super(AncestorsHierarchySet, self).__init__(member.dimension, member.hierarchy)
        self.member = member

    def to_mdx(self) -> str:
        return f"{{{self.member.unique_name}.ANCESTORS}}"


class AncestorHierarchySet(MdxHierarchySet):

    def __init__(self, member: Member, ancestor: int):
        super(AncestorHierarchySet, self).__init__(member.dimension, member.hierarchy)
        self.member = member
        self.ancestor = ancestor

    def to_mdx(self) -> str:
        return f"{{ANCESTOR({self.member.unique_name},{str(self.ancestor)})}}"


class ChildrenHierarchySet(MdxHierarchySet):

    def __init__(self, member: Member):
        super(ChildrenHierarchySet, self).__init__(member.dimension, member.hierarchy)
        self.member = member

    def to_mdx(self) -> str:
        return f"{{{self.member.unique_name}.CHILDREN}}"


class DrillDownLevelHierarchySet(MdxHierarchySet):

    def __init__(self, member: Member):
        super(DrillDownLevelHierarchySet, self).__init__(member.dimension, member.hierarchy)
        self.member = member

    def to_mdx(self) -> str:
        return f"{{DRILLDOWNLEVEL({{{self.member.unique_name}}})}}"


class DescendantsHierarchySet(MdxHierarchySet):

    def __init__(self, member: Member):
        super(DescendantsHierarchySet, self).__init__(member.dimension, member.hierarchy)
        self.member = member

    def to_mdx(self) -> str:
        return f"{{DESCENDANTS({self.member.unique_name})}}"


class Tm1SubsetToSetHierarchySet(MdxHierarchySet):
    def __init__(self, dimension: str, hierarchy: str, subset: str):
        super(Tm1SubsetToSetHierarchySet, self).__init__(dimension, hierarchy)
        self.subset = subset

    def to_mdx(self) -> str:
        return f"{{TM1SUBSETTOSET([{self.dimension}].[{self.hierarchy}],'{self.subset}')}}"


class FilterByAttributeHierarchySet(MdxHierarchySet):

    def __init__(self, underlying_hierarchy_set: MdxHierarchySet, attribute_name: str, attribute_values: List[str]):
        super(FilterByAttributeHierarchySet, self).__init__(underlying_hierarchy_set.dimension,
                                                            underlying_hierarchy_set.hierarchy)
        self.underlying_hierarchy_set = underlying_hierarchy_set
        self.attribute_name = attribute_name
        self.attribute_values = attribute_values

    def to_mdx(self) -> str:
        element_attribute_cube = ELEMENT_ATTRIBUTE_PREFIX + self.dimension

        adjusted_values = [f"'{value}'" if isinstance(value, str) else str(value)
                           for value
                           in self.attribute_values]

        mdx_filter = " OR ".join(
            f"[{element_attribute_cube}].([{element_attribute_cube}].[{self.attribute_name}])={value}"
            for value
            in adjusted_values)

        return f"{{FILTER({self.underlying_hierarchy_set.to_mdx()},{mdx_filter})}}"


class Tm1FilterByPattern(MdxHierarchySet):

    def __init__(self, underlying_hierarchy_set: MdxHierarchySet, wildcard: str):
        super(Tm1FilterByPattern, self).__init__(underlying_hierarchy_set.dimension, underlying_hierarchy_set.hierarchy)
        self.underlying_hierarchy_set = underlying_hierarchy_set
        self.wildcard = wildcard

    def to_mdx(self) -> str:
        return f"{{TM1FILTERBYPATTERN({self.underlying_hierarchy_set.to_mdx()},'{self.wildcard}')}}"


class Tm1FilterByLevelHierarchySet(MdxHierarchySet):

    def __init__(self, underlying_hierarchy_set: MdxHierarchySet, level: int):
        super(Tm1FilterByLevelHierarchySet, self).__init__(underlying_hierarchy_set.dimension,
                                                           underlying_hierarchy_set.hierarchy)
        self.underlying_hierarchy_set = underlying_hierarchy_set
        self.level = level

    def to_mdx(self) -> str:
        return f"{{TM1FILTERBYLEVEL({self.underlying_hierarchy_set.to_mdx()},{self.level})}}"


class FilterByCellValueHierarchySet(MdxHierarchySet):

    def __init__(self, underlying_hierarchy_set: MdxHierarchySet, cube: str, mdx_tuple: MdxTuple, operator, value):
        super(FilterByCellValueHierarchySet, self).__init__(
            underlying_hierarchy_set.dimension,
            underlying_hierarchy_set.hierarchy)
        self.underlying_hierarchy_set = underlying_hierarchy_set
        self.cube = normalize(cube)
        self.mdx_tuple = mdx_tuple
        self.operator = operator
        self.value = value

    def to_mdx(self) -> str:
        adjusted_value = f"'{self.value}'" if isinstance(self.value, str) else self.value
        return f"{{FILTER({self.underlying_hierarchy_set.to_mdx()},[{self.cube}].{self.mdx_tuple.to_mdx()}{self.operator}{adjusted_value})}}"


class OrderByCellValueHierarchySet(MdxHierarchySet):

    def __init__(self, underlying_hierarchy_set: MdxHierarchySet, cube: str, mdx_tuple: MdxTuple):
        super(OrderByCellValueHierarchySet, self).__init__(underlying_hierarchy_set.dimension,
                                                           underlying_hierarchy_set.hierarchy)
        self.underlying_hierarchy_set = underlying_hierarchy_set
        self.cube = normalize(cube)
        self.mdx_tuple = mdx_tuple

    def to_mdx(self) -> str:
        return f"{{ORDER({self.underlying_hierarchy_set.to_mdx()},[{self.cube}].{self.mdx_tuple.to_mdx()})}}"


class Tm1SortHierarchySet(MdxHierarchySet):

    def __init__(self, underlying_hierarchy_set: MdxHierarchySet, ascending: bool):
        super(Tm1SortHierarchySet, self).__init__(underlying_hierarchy_set.dimension,
                                                  underlying_hierarchy_set.hierarchy)
        self.underlying_hierarchy_set = underlying_hierarchy_set
        self.ascending = ascending

    def to_mdx(self) -> str:
        return f"{{TM1SORT({self.underlying_hierarchy_set.to_mdx()},{'ASC' if self.ascending else 'DESC'})}}"


class HeadHierarchySet(MdxHierarchySet):

    def __init__(self, underlying_hierarchy_set: MdxHierarchySet, head: int):
        super(HeadHierarchySet, self).__init__(underlying_hierarchy_set.dimension, underlying_hierarchy_set.hierarchy)
        self.underlying_hierarchy_set = underlying_hierarchy_set
        self.head = head

    def to_mdx(self) -> str:
        return f"{{HEAD({self.underlying_hierarchy_set.to_mdx()},{self.head})}}"


class TailHierarchySet(MdxHierarchySet):

    def __init__(self, underlying_hierarchy_set: MdxHierarchySet, tail: int):
        super(TailHierarchySet, self).__init__(underlying_hierarchy_set.dimension, underlying_hierarchy_set.hierarchy)
        self.underlying_hierarchy_set = underlying_hierarchy_set
        self.tail = tail

    def to_mdx(self) -> str:
        return f"{{TAIL({self.underlying_hierarchy_set.to_mdx()},{self.tail})}}"


class SubsetHierarchySet(MdxHierarchySet):

    def __init__(self, underlying_hierarchy_set: MdxHierarchySet, start: int, length: int):
        super(SubsetHierarchySet, self).__init__(underlying_hierarchy_set.dimension, underlying_hierarchy_set.hierarchy)
        self.underlying_hierarchy_set = underlying_hierarchy_set
        self.start = start
        self.length = length

    def to_mdx(self) -> str:
        return f"{{SUBSET({self.underlying_hierarchy_set.to_mdx()},{self.start},{self.length})}}"


class UnionHierarchySet(MdxHierarchySet):

    def __init__(self, underlying_hierarchy_set: MdxHierarchySet, other_hierarchy_set: MdxHierarchySet):
        super(UnionHierarchySet, self).__init__(underlying_hierarchy_set.dimension, underlying_hierarchy_set.hierarchy)
        self.underlying_hierarchy_set = underlying_hierarchy_set
        self.other_hierarchy_set = other_hierarchy_set

    def to_mdx(self) -> str:
        return f"{{UNION({self.underlying_hierarchy_set.to_mdx()},{self.other_hierarchy_set.to_mdx()})}}"


class IntersectHierarchySet(MdxHierarchySet):

    def __init__(self, underlying_hierarchy_set: MdxHierarchySet, other_hierarchy_set: MdxHierarchySet):
        super(IntersectHierarchySet, self).__init__(underlying_hierarchy_set.dimension,
                                                    underlying_hierarchy_set.hierarchy)
        self.underlying_hierarchy_set = underlying_hierarchy_set
        self.other_hierarchy_set = other_hierarchy_set

    def to_mdx(self) -> str:
        return f"{{INTERSECT({self.underlying_hierarchy_set.to_mdx()},{self.other_hierarchy_set.to_mdx()})}}"


class ExceptHierarchySet(MdxHierarchySet):

    def __init__(self, underlying_hierarchy_set: MdxHierarchySet, other_hierarchy_set: MdxHierarchySet):
        super(ExceptHierarchySet, self).__init__(underlying_hierarchy_set.dimension, underlying_hierarchy_set.hierarchy)
        self.underlying_hierarchy_set = underlying_hierarchy_set
        self.other_hierarchy_set = other_hierarchy_set

    def to_mdx(self) -> str:
        return f"{{EXCEPT({self.underlying_hierarchy_set.to_mdx()},{self.other_hierarchy_set.to_mdx()})}}"


class TopCountHierarchySet(MdxHierarchySet):

    def __init__(self, underlying_hierarchy_set: MdxHierarchySet, cube: str, mdx_tuple: MdxTuple, top: int):
        super(TopCountHierarchySet, self).__init__(
            underlying_hierarchy_set.dimension,
            underlying_hierarchy_set.hierarchy)
        self.underlying_hierarchy_set = underlying_hierarchy_set
        self.cube = normalize(cube)
        self.mdx_tuple = mdx_tuple
        self.top = top

    def to_mdx(self) -> str:
        return f"{{TOPCOUNT({self.underlying_hierarchy_set.to_mdx()},{self.top},[{self.cube}].{self.mdx_tuple.to_mdx()})}}"


class BottomCountHierarchySet(MdxHierarchySet):

    def __init__(self, underlying_hierarchy_set: MdxHierarchySet, cube: str, mdx_tuple: MdxTuple, top: int):
        super(BottomCountHierarchySet, self).__init__(
            underlying_hierarchy_set.dimension,
            underlying_hierarchy_set.hierarchy)
        self.underlying_hierarchy_set = underlying_hierarchy_set
        self.cube = normalize(cube)
        self.mdx_tuple = mdx_tuple
        self.top = top

    def to_mdx(self) -> str:
        return f"{{BOTTOMCOUNT({self.underlying_hierarchy_set.to_mdx()},{self.top},[{self.cube}].{self.mdx_tuple.to_mdx()})}}"


class MdxAxis:
    def __init__(self):
        self.tuples = list()
        self.dim_sets = list()
        self.non_empty = False

    @staticmethod
    def empty() -> 'MdxAxis':
        return MdxAxis()

    def add_tuple(self, mdx_tuple: MdxTuple):
        if bool(self.dim_sets):
            raise ValueError("Can not add tuple to axis that contains sets")

        self.tuples.append(mdx_tuple)

    def add_dim_set(self, mdx_hierarchy_set: MdxHierarchySet):
        if bool(self.tuples):
            raise ValueError("Can not add set to axis that contains tuples")

        self.dim_sets.append(mdx_hierarchy_set)

    def is_empty(self) -> bool:
        return not self.dim_sets and not self.tuples

    def set_non_empty(self, non_empty=True):
        self.non_empty = non_empty

    def to_mdx(self) -> str:
        if self.is_empty():
            return "{}"

        return f"""{"NON EMPTY " if self.non_empty else ""}{self.dim_sets_to_mdx() if self.dim_sets else self.tuples_to_mdx()}"""

    def dim_sets_to_mdx(self) -> str:
        return " * ".join(dim_set.to_mdx() for dim_set in self.dim_sets)

    def tuples_to_mdx(self) -> str:
        return f"{{{','.join(tupl.to_mdx() for tupl in self.tuples)}}}"


class MdxBuilder:
    def __init__(self, cube: str):
        self.cube = normalize(cube)
        self.axes = {0: MdxAxis.empty()}
        self.where = MdxTuple.empty()

    @staticmethod
    def from_cube(cube: str) -> 'MdxBuilder':
        return MdxBuilder(cube)

    def columns_non_empty(self) -> 'MdxBuilder':
        return self.axis_non_empty(0)

    def rows_non_empty(self) -> 'MdxBuilder':
        return self.axis_non_empty(1)

    def axis_non_empty(self, axis: int) -> 'MdxBuilder':
        if axis not in self.axes:
            self.axes[axis] = MdxAxis.empty()

        self.axes[axis].set_non_empty()
        return self

    def _add_tuple_to_axis(self, axis: MdxAxis, *args: Member) -> 'MdxBuilder':
        mdx_tuple = MdxTuple.of(*args)
        axis.add_tuple(mdx_tuple)
        return self

    def add_member_tuple_to_axis(self, axis: int, *args: Member):
        if axis not in self.axes:
            self.axes[axis] = MdxAxis.empty()
        return self._add_tuple_to_axis(self.axes[axis], *args)

    def add_member_tuple_to_columns(self, *args: Member) -> 'MdxBuilder':
        return self.add_member_tuple_to_axis(0, *args)

    def add_member_tuple_to_rows(self, *args: Member) -> 'MdxBuilder':
        return self.add_member_tuple_to_axis(1, *args)

    def add_hierarchy_set_to_row_axis(self, mdx_hierarchy_set: MdxHierarchySet) -> 'MdxBuilder':
        return self.add_hierarchy_set_to_axis(1, mdx_hierarchy_set)

    def add_hierarchy_set_to_column_axis(self, mdx_hierarchy_set: MdxHierarchySet) -> 'MdxBuilder':
        return self.add_hierarchy_set_to_axis(0, mdx_hierarchy_set)

    def add_hierarchy_set_to_axis(self, axis: int, mdx_hierarchy_set: MdxHierarchySet) -> 'MdxBuilder':
        if axis not in self.axes:
            self.axes[axis] = MdxAxis.empty()

        self.axes[axis].add_dim_set(mdx_hierarchy_set)
        return self

    def add_member_to_where(self, member: Member) -> 'MdxBuilder':
        self.where.add_member(member)
        return self

    def add_members_to_where(self, *args: Member) -> 'MdxBuilder':
        for member in args:
            self.add_member_to_where(member)
        return self

    def to_mdx(self) -> str:
        mdx_axes = ",".join(
            f"{'' if axis.is_empty() else (axis.to_mdx() + ' ON ' + str(position))}"
            for position, axis
            in self.axes.items())

        return f"""SELECT {mdx_axes} FROM [{self.cube}] {"WHERE " + self.where.to_mdx() if not self.where.is_empty() else ""}"""
