import os
from abc import abstractmethod
from enum import Enum
from typing import List, Optional, Union

from ordered_set import OrderedSet

ELEMENT_ATTRIBUTE_PREFIX = "}ELEMENTATTRIBUTES_"


class Order(Enum):
    ASC = 1
    DESC = 2
    BASC = 3
    BDESC = 4

    def __str__(self):
        return self.name

    @classmethod
    def _missing_(cls, value: str):
        for member in cls:
            if member.name.lower() == value.replace(" ", "").lower():
                return member
        # default
        raise ValueError(f"Invalid order type: '{value}'")


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
    def from_unique_name(unique_name: str) -> 'Member':
        dimension = Member.dimension_name_from_unique_name(unique_name)
        element = Member.element_name_from_unique_name(unique_name)
        if unique_name.count("].[") == 1:
            return Member(dimension, dimension, element)

        elif unique_name.count("].[") == 2:
            hierarchy = Member.hierarchy_name_from_unique_name(unique_name)
            return Member(dimension, hierarchy, element)

        else:
            raise ValueError(f"Argument '{unique_name}' must be a valid member unique name")

    @staticmethod
    def of(*args: str) -> 'Member':
        # case: '[dim].[elem]'
        if len(args) == 1:
            return Member.from_unique_name(args[0])
        elif len(args) == 2:
            return Member(args[0], args[0], args[1])
        elif len(args) == 3:
            return Member(*args)
        else:
            raise ValueError("method takes either one, two or three str arguments")

    @staticmethod
    def dimension_name_from_unique_name(element_unique_name: str) -> str:
        return element_unique_name[1:element_unique_name.find('].[')]

    @staticmethod
    def hierarchy_name_from_unique_name(element_unique_name: str) -> str:
        return element_unique_name[element_unique_name.find('].[') + 3:element_unique_name.rfind('].[')]

    @staticmethod
    def element_name_from_unique_name(element_unique_name: str) -> str:
        return element_unique_name[element_unique_name.rfind('].[') + 3:-1]

    def __eq__(self, other) -> bool:
        return self.unique_name == other.unique_name

    def __hash__(self):
        return hash(self.unique_name)


class CalculatedMember(Member):
    def __init__(self, dimension: str, hierarchy: str, element: str, calculation: str):
        super(CalculatedMember, self).__init__(dimension, hierarchy, element)
        self.calculation = calculation

    @staticmethod
    def avg(dimension: str, hierarchy: str, element: str, cube: str, mdx_set: 'MdxHierarchySet',
            mdx_tuple: 'MdxTuple'):
        calculation = f"AVG({mdx_set.to_mdx()},[{cube.upper()}].{mdx_tuple.to_mdx()})"
        return CalculatedMember(dimension, hierarchy, element, calculation)

    @staticmethod
    def sum(dimension: str, hierarchy: str, element: str, cube: str, mdx_set: 'MdxHierarchySet',
            mdx_tuple: 'MdxTuple'):
        calculation = f"SUM({mdx_set.to_mdx()},[{cube.upper()}].{mdx_tuple.to_mdx()})"
        return CalculatedMember(dimension, hierarchy, element, calculation)

    @staticmethod
    def lookup(dimension: str, hierarchy: str, element: str, cube: str, mdx_tuple: 'MdxTuple'):
        calculation = f"[{cube.upper()}].{mdx_tuple.to_mdx()}"
        return CalculatedMember(dimension, hierarchy, element, calculation)

    @staticmethod
    def lookup_attribute(dimension: str, hierarchy: str, element: str, attribute_dimension: str, attribute: str):
        attribute_cube = ELEMENT_ATTRIBUTE_PREFIX + attribute_dimension.upper()
        calculation = f"[{attribute_cube}].([{attribute_cube}].[{attribute.upper()}])"
        return CalculatedMember(dimension, hierarchy, element, calculation)

    def to_mdx(self):
        return f"MEMBER {self.unique_name} AS {self.calculation}"


class MdxTuple:

    def __init__(self, members):
        self.members = OrderedSet(members)

    @staticmethod
    def of(*args: Union[str, Member]) -> 'MdxTuple':
        # handle unique element names
        members = [Member.of(member)
                   if isinstance(member, str) else member
                   for member in args]
        mdx_tuple = MdxTuple(members)
        return mdx_tuple

    @staticmethod
    def empty() -> 'MdxTuple':
        return MdxTuple.of()

    def add_member(self, member: Union[str, Member]):
        if isinstance(member, str):
            member = Member.of(member)
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

    def to_clipboard(self):
        mdx = self.to_mdx()
        command = 'echo | set /p nul="' + mdx + '"| clip'
        os.system(command)
        print(mdx)

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
    def tm1_dimension_subset_to_set(dimension: str, subset: str) -> 'MdxHierarchySet':
        return Tm1SubsetToSetHierarchySet(dimension, dimension, subset)

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
    def member(member: Union[str, Member]) -> 'MdxHierarchySet':
        if isinstance(member, str):
            member = Member.of(member)
        return ElementsHierarchySet(member)

    @staticmethod
    def members(members: List[Union[str, Member]]) -> 'MdxHierarchySet':
        members = [
            Member.of(member)
            if isinstance(member, str) else member
            for member in members]
        return ElementsHierarchySet(*members)

    @staticmethod
    def unions(sets: List['MdxHierarchySet'], allow_duplicates: bool = False) -> 'MdxHierarchySet':
        return UnionsManyHierarchySet(sets, allow_duplicates)

    @staticmethod
    def parent(member: Union[str, Member]) -> 'MdxHierarchySet':
        if isinstance(member, str):
            member = Member.of(member)
        return ParentHierarchySet(member)

    @staticmethod
    def first_child(member: Union[str, Member]) -> 'MdxHierarchySet':
        if isinstance(member, str):
            member = Member.of(member)
        return FirstChildHierarchySet(member)

    @staticmethod
    def last_child(member: Union[str, Member]) -> 'MdxHierarchySet':
        if isinstance(member, str):
            member = Member.of(member)
        return LastChildHierarchySet(member)

    @staticmethod
    def children(member: Union[str, Member]) -> 'MdxHierarchySet':
        if isinstance(member, str):
            member = Member.of(member)
        return ChildrenHierarchySet(member)

    @staticmethod
    def ancestors(member: Union[str, Member]) -> 'MdxHierarchySet':
        if isinstance(member, str):
            member = Member.of(member)
        return AncestorsHierarchySet(member)

    @staticmethod
    def ancestor(member: Union[str, Member], ancestor: int) -> 'MdxHierarchySet':
        if isinstance(member, str):
            member = Member.of(member)
        return AncestorHierarchySet(member, ancestor)

    @staticmethod
    def drill_down_level(member: Union[str, Member]) -> 'MdxHierarchySet':
        if isinstance(member, str):
            member = Member.of(member)
        return DrillDownLevelHierarchySet(member)

    @staticmethod
    def descendants(member: Union[str, Member]) -> 'MdxHierarchySet':
        if isinstance(member, str):
            member = Member.of(member)
        return DescendantsHierarchySet(member)

    @staticmethod
    def from_str(dimension: str, hierarchy: str, mdx: str):
        return StrHierarchySet(dimension, hierarchy, mdx)

    def filter_by_attribute(self, attribute_name: str, attribute_values: List,
                            operator: Optional[str] = '=') -> 'MdxHierarchySet':
        return FilterByAttributeHierarchySet(self, attribute_name, attribute_values, operator)

    def filter_by_pattern(self, wildcard: str) -> 'MdxHierarchySet':
        return Tm1FilterByPattern(self, wildcard)

    def filter_by_level(self, level: int) -> 'MdxHierarchySet':
        return Tm1FilterByLevelHierarchySet(self, level)

    def filter_by_cell_value(self, cube: str, mdx_tuple: MdxTuple, operator: str, value) -> 'MdxHierarchySet':
        return FilterByCellValueHierarchySet(self, cube, mdx_tuple, operator, value)

    def filter_by_instr(self, cube: str, mdx_tuple: MdxTuple, substring: str, operator: str = ">", position: int = "0",
                        case_insensitive=True):
        return FilterByInstr(self, cube, mdx_tuple, substring, operator, position, case_insensitive)

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

    def union(self, other_set: 'MdxHierarchySet', allow_duplicates: bool = False) -> 'MdxHierarchySet':
        return UnionHierarchySet(self, other_set, allow_duplicates)

    def intersect(self, other_set: 'MdxHierarchySet') -> 'MdxHierarchySet':
        return IntersectHierarchySet(self, other_set)

    # avoid conflict with reserved word `except`
    def except_(self, other_set: 'MdxHierarchySet') -> 'MdxHierarchySet':
        return ExceptHierarchySet(self, other_set)

    def order(self, cube: str, mdx_tuple: MdxTuple, order: Union[str, Order] = Order.BASC) -> 'MdxHierarchySet':
        return OrderByCellValueHierarchySet(self, cube, mdx_tuple, order)

    def order_by_attribute(self, attribute_name: str, order: Union[Order, str] = Order.BASC) -> 'MdxHierarchySet':
        return OrderByAttributeValueHierarchySet(self, attribute_name, order)

    def generate_attribute_to_member(self, attribute: str, dimension: str, hierarchy: str = None):
        return GenerateAttributeToMemberSet(self, attribute, dimension, hierarchy)

    def tm1_drill_down_member(self, all: bool = True, other_set: 'MdxHierarchySet' = None,
                              recursive: bool = True) -> 'MdxHierarchySet':
        return Tm1DrillDownMemberSet(self, all, other_set, recursive)


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

class SetsHierarchySet(MdxHierarchySet):

    def __init__(self, *sets: MdxHierarchySet):
        if not sets:
            raise RuntimeError('sets must not be empty')

        super(SetsHierarchySet, self).__init__(sets[0].dimension, sets[0].hierarchy)
        self.sets = sets

    def to_mdx(self) -> str:
        return f"{{{','.join(set_.to_mdx() for set_ in self.sets)}}}"


class UnionsManyHierarchySet(MdxHierarchySet):

    def __init__(self, sets: List[MdxHierarchySet], allow_duplicates: bool = False):
        super(UnionsManyHierarchySet, self).__init__(sets[0].dimension, sets[0].hierarchy)
        self.sets = sets
        self.allow_duplicates = allow_duplicates

    def to_mdx(self) -> str:
        if self.allow_duplicates:
            return f"{{{','.join(set_.to_mdx() for set_ in self.sets)}}}"
        else:
            return f"{{{' + '.join(set_.to_mdx() for set_ in self.sets)}}}"


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


class Tm1DrillDownMemberSet(MdxHierarchySet):

    def __init__(self, underlying_hierarchy_set: MdxHierarchySet, all: bool = True, other_set: 'MdxHierarchySet' = None,
                 recursive: bool = True):
        super(Tm1DrillDownMemberSet, self).__init__(underlying_hierarchy_set.dimension,
                                                    underlying_hierarchy_set.hierarchy)
        self.underlying_hierarchy_set = underlying_hierarchy_set
        if other_set:
            self.set2 = other_set
        else:
            self.set2 = "ALL"

        if recursive:
            self.recursive = ", RECURSIVE"
        else:
            self.recursive = ""

    def to_mdx(self) -> str:
        if self.set2 == "ALL":
            return f"{{TM1DRILLDOWNMEMBER({self.underlying_hierarchy_set.to_mdx()}, {self.set2}{self.recursive})}}"
        else:
            return f"{{TM1DRILLDOWNMEMBER({self.underlying_hierarchy_set.to_mdx()}, {self.set2.to_mdx()}{self.recursive})}}"


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
        return f'{{TM1SUBSETTOSET([{self.dimension}].[{self.hierarchy}],"{self.subset}")}}'


class StrHierarchySet(MdxHierarchySet):

    def __init__(self, dimension: str, hierarchy: str, mdx: str):
        super(StrHierarchySet, self).__init__(dimension, hierarchy)
        self._mdx = mdx

    def to_mdx(self) -> str:
        return self._mdx


class FilterByAttributeHierarchySet(MdxHierarchySet):

    def __init__(self, underlying_hierarchy_set: MdxHierarchySet, attribute_name: str, attribute_values: List[str],
                 operator: str = '='):
        super(FilterByAttributeHierarchySet, self).__init__(underlying_hierarchy_set.dimension,
                                                            underlying_hierarchy_set.hierarchy)
        self.underlying_hierarchy_set = underlying_hierarchy_set
        self.attribute_name = attribute_name
        self.attribute_values = attribute_values
        self.operator = operator

    def to_mdx(self) -> str:
        element_attribute_cube = ELEMENT_ATTRIBUTE_PREFIX + self.dimension

        adjusted_values = [f'"{value}"' if isinstance(value, str) else str(value)
                           for value
                           in self.attribute_values]

        mdx_filter = " OR ".join(
            f"[{element_attribute_cube}].([{element_attribute_cube}].[{self.attribute_name}]){self.operator}{value}"
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


class FilterByInstr(MdxHierarchySet):

    def __init__(self, underlying_hierarchy_set, cube: str, mdx_tuple: MdxTuple, substring: str, operator: str = ">",
                 position: int = "0", case_insensitive=True):
        super(FilterByInstr, self).__init__(
            underlying_hierarchy_set.dimension,
            underlying_hierarchy_set.hierarchy)
        self.underlying_hierarchy_set = underlying_hierarchy_set
        self.cube = normalize(cube)
        self.mdx_tuple = mdx_tuple
        self.substring = substring.upper() if case_insensitive else substring
        self.operator = operator
        self.position = position
        self.case_insensitive = case_insensitive

    def to_mdx(self) -> str:
        return f"{{FILTER({self.underlying_hierarchy_set.to_mdx()},INSTR({'UCASE(' if self.case_insensitive else ''}" \
               f"[{self.cube}].{self.mdx_tuple.to_mdx()}{')' if self.case_insensitive else ''},'{self.substring}')" \
               f"{self.operator}{self.position})}}"


class OrderByCellValueHierarchySet(MdxHierarchySet):

    def __init__(self, underlying_hierarchy_set: MdxHierarchySet, cube: str, mdx_tuple: MdxTuple,
                 order: Union[Order, str] = Order.BASC):
        super(OrderByCellValueHierarchySet, self).__init__(underlying_hierarchy_set.dimension,
                                                           underlying_hierarchy_set.hierarchy)
        self.underlying_hierarchy_set = underlying_hierarchy_set
        self.cube = normalize(cube)
        self.mdx_tuple = mdx_tuple
        self.order = Order(order)

    def to_mdx(self) -> str:
        return f"{{ORDER({self.underlying_hierarchy_set.to_mdx()},[{self.cube}].{self.mdx_tuple.to_mdx()},{self.order})}}"


class OrderByAttributeValueHierarchySet(MdxHierarchySet):

    def __init__(self, underlying_hierarchy_set: MdxHierarchySet, attribute_name: str,
                 order: Union[str, Order] = Order.BASC):
        super(OrderByAttributeValueHierarchySet, self).__init__(underlying_hierarchy_set.dimension,
                                                                underlying_hierarchy_set.hierarchy)
        self.underlying_hierarchy_set = underlying_hierarchy_set
        self.attribute_name = normalize(attribute_name)
        self.order = Order(order)

    def to_mdx(self) -> str:
        return f"{{ORDER({self.underlying_hierarchy_set.to_mdx()},[{self.underlying_hierarchy_set.dimension}].[{self.underlying_hierarchy_set.hierarchy}].CURRENTMEMBER.PROPERTIES(\"{self.attribute_name}\"), {self.order})}}"


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

    def __init__(self, underlying_hierarchy_set: MdxHierarchySet, other_hierarchy_set: MdxHierarchySet, allow_duplicates: bool):
        super(UnionHierarchySet, self).__init__(underlying_hierarchy_set.dimension, underlying_hierarchy_set.hierarchy)
        self.underlying_hierarchy_set = underlying_hierarchy_set
        self.other_hierarchy_set = other_hierarchy_set
        self.allow_duplicates = allow_duplicates

    def to_mdx(self) -> str:
        return f"{{UNION({self.underlying_hierarchy_set.to_mdx()},{self.other_hierarchy_set.to_mdx()}{', ALL' if self.allow_duplicates else ''})}}"


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


class GenerateAttributeToMemberSet(MdxHierarchySet):

    def __init__(self, underlying_hierarchy_set: MdxHierarchySet, attribute: str, dimension: str, hierarchy: str):
        super(GenerateAttributeToMemberSet, self).__init__(
            underlying_hierarchy_set.dimension,
            underlying_hierarchy_set.hierarchy)
        self.underlying_hierarchy_set = underlying_hierarchy_set
        self.dimension = dimension.upper()
        self.hierarchy = hierarchy.upper() if hierarchy else self.dimension
        self.attribute = attribute

    def to_mdx(self) -> str:
        return f"{{GENERATE({self.underlying_hierarchy_set.to_mdx()}," \
               f"{{STRTOMEMBER('[{self.dimension}].[{self.hierarchy}].[' + [{self.underlying_hierarchy_set.dimension}].[{self.underlying_hierarchy_set.hierarchy}].CURRENTMEMBER.PROPERTIES(\"{self.attribute}\") + ']')}})}}"


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

    def set_non_empty(self, non_empty: bool = True):
        self.non_empty = non_empty

    def to_mdx(self, tm1_ignore_bad_tuples=False) -> str:
        if self.is_empty():
            return "{}"

        return f"""{"NON EMPTY " if self.non_empty else ""}{"TM1IGNORE_BADTUPLES " if tm1_ignore_bad_tuples else ""}{self.dim_sets_to_mdx() if self.dim_sets else self.tuples_to_mdx()}"""

    def dim_sets_to_mdx(self) -> str:
        return " * ".join(dim_set.to_mdx() for dim_set in self.dim_sets)

    def tuples_to_mdx(self) -> str:
        return f"{{{','.join(tupl.to_mdx() for tupl in self.tuples)}}}"


class MdxBuilder:
    def __init__(self, cube: str):
        self.cube = normalize(cube)
        self.axes = {0: MdxAxis.empty()}
        self._where = MdxTuple.empty()
        self.calculated_members = list()
        self._tm1_ignore_bad_tuples = False

    @staticmethod
    def from_cube(cube: str) -> 'MdxBuilder':
        return MdxBuilder(cube)

    def with_member(self, member: CalculatedMember) -> 'MdxBuilder':
        self.calculated_members.append(member)
        return self

    def columns_non_empty(self) -> 'MdxBuilder':
        return self.non_empty(0)

    def rows_non_empty(self) -> 'MdxBuilder':
        return self.non_empty(1)

    def non_empty(self, axis: int) -> 'MdxBuilder':
        if axis not in self.axes:
            self.axes[axis] = MdxAxis.empty()

        self.axes[axis].set_non_empty()
        return self

    def tm1_ignore_bad_tuples(self, ignore=True) -> 'MdxBuilder':
        self._tm1_ignore_bad_tuples = ignore
        return self

    def _add_tuple_to_axis(self, axis: MdxAxis, *args: Union[str, Member]) -> 'MdxBuilder':
        mdx_tuple = MdxTuple.of(*args)
        axis.add_tuple(mdx_tuple)
        return self

    def add_member_tuple_to_axis(self, axis: int, *args: Union[str, Member]) -> 'MdxBuilder':
        if axis not in self.axes:
            self.axes[axis] = MdxAxis.empty()
        return self._add_tuple_to_axis(self.axes[axis], *args)

    def add_member_tuple_to_columns(self, *args: Union[str, Member]) -> 'MdxBuilder':
        return self.add_member_tuple_to_axis(0, *args)

    def add_member_tuple_to_rows(self, *args: Union[str, Member]) -> 'MdxBuilder':
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

    def add_empty_set_to_axis(self, axis: int):
        if axis in self.axes:
            raise ValueError(f"axis: '{axis}' must be empty")

        hierarchy_set = MdxHierarchySet.from_str("", "", "{}")
        return self.add_hierarchy_set_to_axis(axis, hierarchy_set)

    def add_member_to_where(self, member: Union[str, Member]) -> 'MdxBuilder':
        self._where.add_member(member)
        return self

    def where(self, *args: Union[str, Member]) -> 'MdxBuilder':
        for member in args:
            if isinstance(member, str):
                member = Member.of(member)
            if not isinstance(member, Member):
                raise ValueError(f"Argument '{member}' must be of type str or Member")
            self.add_member_to_where(member)
        return self

    def to_mdx(self) -> str:
        mdx_with = "WITH\r\n" + "\r\n".join(
            calculated_member.to_mdx()
            for calculated_member
            in self.calculated_members) + "\r\n"

        mdx_axes = ",\r\n".join(
            f"{'' if axis.is_empty() else (axis.to_mdx(self._tm1_ignore_bad_tuples) + ' ON ' + str(position))}"
            for position, axis
            in self.axes.items())

        mdx_where = "\r\nWHERE " + self._where.to_mdx() if not self._where.is_empty() else ""

        return f"""{mdx_with if self.calculated_members else ""}SELECT\r\n{mdx_axes}\r\nFROM [{self.cube}]{mdx_where}"""

    def to_clipboard(self):
        mdx = self.to_mdx()
        mdx = mdx.replace('\r\n', ' ')
        command = 'echo | set /p nul="' + mdx + '"| clip'
        os.system(command)
        print(mdx)
