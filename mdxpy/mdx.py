import os
from abc import abstractmethod
from enum import Enum
from typing import List, Optional, Union, Iterable

ELEMENT_ATTRIBUTE_PREFIX = "}ELEMENTATTRIBUTES_"


class DescFlag(Enum):
    SELF = 1
    AFTER = 2
    BEFORE = 3
    BEFORE_AND_AFTER = 4
    SELF_AND_AFTER = 5
    SELF_AND_BEFORE = 6
    SELF_BEFORE_AFTER = 7
    LEAVES = 8

    def __str__(self):
        return self.name

    @classmethod
    def _missing_(cls, value: str):
        if value is None:
            return None
        for member in cls:
            if member.name.lower() == value.replace(" ", "").lower():
                return member
        # default
        raise ValueError(f"Invalid Desc Flag type: '{value}'")


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


class ElementType(Enum):
    NUMERIC = 1
    STRING = 2
    CONSOLIDATED = 3

    def __str__(self):
        return self.name

    @classmethod
    def _missing_(cls, value: str):
        for member in cls:
            if member.name.lower() == value.replace(" ", "").lower():
                return member
        # default
        raise ValueError(f"Invalid element type: '{value}'")


def normalize(name: str) -> str:
    return name.lower().replace(" ", "").replace("]", "]]")


class Member:
    # control if full element unique name is used for members without explicit hierarchy
    SHORT_NOTATION = False

    def __init__(self, dimension: str, hierarchy: str, element: str):
        self.dimension = dimension
        self.hierarchy = hierarchy
        self.element = element
        self.unique_name = self.build_unique_name(dimension, hierarchy, element)

    @classmethod
    def build_unique_name(cls, dimension, hierarchy, element) -> str:
        if cls.SHORT_NOTATION and dimension == hierarchy:
            return f"[{normalize(dimension)}].[{normalize(element)}]"
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


class DimensionProperty(Member):
    SHORT_NOTATION = False

    def __init__(self, dimension: str, hierarchy: str, attribute: str):
        super(DimensionProperty, self).__init__(dimension, hierarchy, attribute)

    @staticmethod
    def from_unique_name(unique_name: str) -> 'DimensionProperty':
        dimension = Member.dimension_name_from_unique_name(unique_name)
        attribute = Member.element_name_from_unique_name(unique_name)
        if unique_name.count("].[") == 1:
            return DimensionProperty(dimension, dimension, attribute)

        elif unique_name.count("].[") == 2:
            hierarchy = Member.hierarchy_name_from_unique_name(unique_name)
            return DimensionProperty(dimension, hierarchy, attribute)

        else:
            raise ValueError(f"Argument '{unique_name}' must be a valid DimensionProperty unique name")

    @staticmethod
    def of(*args: str) -> 'DimensionProperty':
        # case: '[dim].[elem]'
        if len(args) == 1:
            return DimensionProperty.from_unique_name(args[0])
        elif len(args) == 2:
            return DimensionProperty(args[0], args[0], args[1])
        elif len(args) == 3:
            return DimensionProperty(*args)
        else:
            raise ValueError("method takes either one, two or three str arguments")


class CalculatedMember(Member):
    def __init__(self, dimension: str, hierarchy: str, element: str, calculation: str):
        super(CalculatedMember, self).__init__(dimension, hierarchy, element)
        self.calculation = calculation

    @staticmethod
    def avg(dimension: str, hierarchy: str, element: str, cube: str, mdx_set: 'MdxHierarchySet',
            mdx_tuple: 'MdxTuple'):
        calculation = f"AVG({mdx_set.to_mdx()},[{cube.lower()}].{mdx_tuple.to_mdx()})"
        return CalculatedMember(dimension, hierarchy, element, calculation)

    @staticmethod
    def sum(dimension: str, hierarchy: str, element: str, cube: str, mdx_set: 'MdxHierarchySet',
            mdx_tuple: 'MdxTuple'):
        calculation = f"SUM({mdx_set.to_mdx()},[{cube.lower()}].{mdx_tuple.to_mdx()})"
        return CalculatedMember(dimension, hierarchy, element, calculation)

    @staticmethod
    def lookup(dimension: str, hierarchy: str, element: str, cube: str, mdx_tuple: 'MdxTuple'):
        calculation = f"[{cube.lower()}].{mdx_tuple.to_mdx()}"
        return CalculatedMember(dimension, hierarchy, element, calculation)

    @staticmethod
    def lookup_attribute(dimension: str, hierarchy: str, element: str, attribute_dimension: str, attribute: str):
        attribute_cube = ELEMENT_ATTRIBUTE_PREFIX + attribute_dimension.lower()
        calculation = f"[{attribute_cube}].([{attribute_cube}].[{attribute.lower()}])"
        return CalculatedMember(dimension, hierarchy, element, calculation)

    def to_mdx(self):
        return f"MEMBER {self.unique_name} AS {self.calculation}"


class MdxLevelExpression:

    def __init__(self, dimension: str, hierarchy: Optional[str] = None):
        self.dimension = normalize(dimension)
        self.hierarchy = normalize(hierarchy) if hierarchy else self.dimension

    @abstractmethod
    def to_mdx(self) -> str:
        pass

    @staticmethod
    def level_number(level: int, dimension: str, hierarchy: str = None) -> 'MdxLevelExpression':
        return LevelNumberExpression(level, dimension, hierarchy)

    @staticmethod
    def level_name(level: str, dimension: str, hierarchy: str = None) -> 'MdxLevelExpression':
        return LevelNameExpression(level, dimension, hierarchy)

    @staticmethod
    def member_level(member: Union[str, Member]) -> 'MdxLevelExpression':
        return MemberLevelExpression(member)


class LevelNumberExpression(MdxLevelExpression):

    def __init__(self, level_number: int, dimension: str, hierarchy: str = None):
        super(LevelNumberExpression, self).__init__(dimension, hierarchy)
        self.level = level_number

    def to_mdx(self) -> str:
        return f"[{self.dimension}].[{self.hierarchy}].LEVELS({self.level})"


class LevelNameExpression(MdxLevelExpression):

    def __init__(self, level_name: str, dimension: str, hierarchy: str = None):
        super(LevelNameExpression, self).__init__(dimension, hierarchy)
        self.level = level_name

    def to_mdx(self) -> str:
        return f"[{self.dimension}].[{self.hierarchy}].LEVELS(\'{self.level}\')"


class MemberLevelExpression(MdxLevelExpression):

    def __init__(self, member: Member):
        super(MemberLevelExpression, self).__init__(member.dimension, member.hierarchy)
        self.member = member

    def to_mdx(self) -> str:
        return f"{self.member.unique_name}.LEVEL"


class MdxTuple:

    def __init__(self, members):
        self.members = list(members)

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
        self.members.append(member)

    def is_empty(self) -> bool:
        return not self.members

    def to_mdx(self) -> str:
        return f"({','.join(member.unique_name for member in self.members)})"

    def __len__(self):
        return len(self.members)


class MdxPropertiesTuple:

    def __init__(self, members):
        self.members = list(members)

    @staticmethod
    def of(*args: Union[str, DimensionProperty]) -> 'MdxPropertiesTuple':
        # handle unique element names
        members = [DimensionProperty.of(member)
                   if isinstance(member, str) else member
                   for member in args]
        mdx_tuple = MdxPropertiesTuple(members)
        return mdx_tuple

    @staticmethod
    def empty() -> 'MdxPropertiesTuple':
        return MdxPropertiesTuple.of()

    def add_member(self, member: Union[str, DimensionProperty]):
        if isinstance(member, str):
            member = DimensionProperty.of(member)
        self.members.append(member)

    def is_empty(self) -> bool:
        return not self.members

    def to_mdx(self) -> str:
        return f"{','.join(member.unique_name for member in self.members)}"

    def __len__(self):
        return len(self.members)


class MdxSet:

    @abstractmethod
    def to_mdx(self) -> str:
        pass

    @staticmethod
    def cross_joins(sets: List['MdxSet']) -> 'MdxSet':
        return CrossJoinMdxSet(sets)

    @staticmethod
    def unions(sets: List['MdxSet'], allow_duplicates: bool = False) -> 'MdxSet':
        return MultiUnionSet(sets, allow_duplicates)

    @staticmethod
    def tuples(tuples: Iterable['MdxTuple']) -> 'MdxSet':
        return TuplesSet(tuples)


class CrossJoinMdxSet(MdxSet):
    def __init__(self, sets: List['MdxSet']):
        if not sets:
            raise RuntimeError('sets must not be empty')
        self.sets = sets

    def to_mdx(self) -> str:
        return f"{{{' * '.join(set_.to_mdx() for set_ in self.sets)}}}"


class TuplesSet(MdxSet):
    def __init__(self, tuples: Iterable[MdxTuple]):
        self.tuples = tuples

    def to_mdx(self) -> str:
        return f"{{ {','.join(tupl.to_mdx() for tupl in self.tuples)} }}"


class MultiUnionSet(MdxSet):

    def __init__(self, sets: List[MdxSet], allow_duplicates: bool = False):
        if not sets:
            raise RuntimeError('sets must not be empty')

        self.sets = sets
        self.allow_duplicates = allow_duplicates

    def to_mdx(self) -> str:
        if self.allow_duplicates:
            return f"{{{','.join(set_.to_mdx() for set_ in self.sets)}}}"
        else:
            return f"{{{' + '.join(set_.to_mdx() for set_ in self.sets)}}}"


class MdxHierarchySet(MdxSet):

    def __init__(self, dimension: str, hierarchy: Optional[str] = None):
        self.dimension = normalize(dimension)
        self.hierarchy = normalize(hierarchy) if hierarchy else self.dimension

    def to_clipboard(self):
        mdx = self.to_mdx()
        command = 'echo | set /p nul="' + mdx + '"| clip'
        os.system(command)
        print(mdx)

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
    def drill_down_level(member: Union[str, Member], level: int) -> 'MdxHierarchySet':
        if isinstance(member, str):
            member = Member.of(member)
        return DrillDownLevelHierarchySet(member, level)

    @staticmethod
    def descendants(member: Union[str, Member], level_or_depth: Union[MdxLevelExpression, int] = None,
                    desc_flag: Union[str, Order] = None) -> 'MdxHierarchySet':
        if isinstance(member, str):
            member = Member.of(member)
        return DescendantsHierarchySet(member, level_or_depth, desc_flag)

    @staticmethod
    def from_str(dimension: str, hierarchy: str, mdx: str):
        return StrHierarchySet(dimension, hierarchy, mdx)

    @staticmethod
    def range(start_member: Union[str, Member], end_member: Union[str, Member]) -> 'MdxHierarchySet':
        if isinstance(start_member, str):
            start_member = Member.of(start_member)
        if isinstance(end_member, str):
            end_member = Member.of(end_member)
        return RangeHierarchySet(start_member, end_member)

    @staticmethod
    def unions(sets: List['MdxHierarchySet'], allow_duplicates: bool = False) -> 'MdxHierarchySet':
        return MultiUnionHierarchySet(sets, allow_duplicates)

    def filter_by_attribute(self, attribute_name: str, attribute_values: List,
                            operator: Optional[str] = '=') -> 'MdxHierarchySet':
        return FilterByAttributeHierarchySet(self, attribute_name, attribute_values, operator)

    def filter_by_pattern(self, wildcard: str) -> 'MdxHierarchySet':
        return Tm1FilterByPattern(self, wildcard)

    def filter_by_level(self, level: int) -> 'MdxHierarchySet':
        return Tm1FilterByLevelHierarchySet(self, level)

    def filter_by_element_type(self, element_type: Union[ElementType, str]) -> 'MdxHierarchySet':
        return Tm1FilterByElementTypeHierarchySet(self, element_type)

    def filter_by_cell_value(self, cube: str, mdx_tuple: MdxTuple, operator: str, value) -> 'MdxHierarchySet':
        return FilterByCellValueHierarchySet(self, cube, mdx_tuple, operator, value)

    def filter_by_instr(self, cube: str, mdx_tuple: MdxTuple, substring: str, operator: str = ">", position: int = "0",
                        case_insensitive=True):
        return FilterByInstr(self, cube, mdx_tuple, substring, operator, position, case_insensitive)

    def tm1_sort(self, ascending=True) -> 'MdxHierarchySet':
        return Tm1SortHierarchySet(self, ascending)

    def hierarchize(self) -> 'MdxHierarchySet':
        return HierarchizeSet(self)

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

    def tm1_drill_down_member(self, other_set: 'MdxHierarchySet' = None,
                              recursive: bool = True) -> 'MdxHierarchySet':
        return Tm1DrillDownMemberSet(self, other_set, recursive)


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


class Tm1DrillDownMemberSet(MdxHierarchySet):

    def __init__(self, underlying_hierarchy_set: MdxHierarchySet, other_set: 'MdxHierarchySet' = None,
                 recursive: bool = True):
        super(Tm1DrillDownMemberSet, self).__init__(
            underlying_hierarchy_set.dimension,
            underlying_hierarchy_set.hierarchy)
        self.underlying_hierarchy_set = underlying_hierarchy_set

        if other_set:
            self.set2 = other_set.to_mdx()
        else:
            self.set2 = "ALL"

        if recursive:
            self.recursive = ", RECURSIVE"
        else:
            self.recursive = ""

    def to_mdx(self) -> str:
        return f"{{TM1DRILLDOWNMEMBER({self.underlying_hierarchy_set.to_mdx()}, {self.set2}{self.recursive})}}"


class DrillDownLevelHierarchySet(MdxHierarchySet):

    def __init__(self, member: Member, level: int =1):
        super(DrillDownLevelHierarchySet, self).__init__(member.dimension, member.hierarchy)
        self.member = member
        self.level = level

    def to_mdx(self) -> str:
        startstring = ''
        endstring = ''
        for _ in range(self.level):
            startstring += 'DRILLDOWNLEVEL('
            endstring += ')'
            
        return f"{{{startstring}{{{self.member.unique_name}}}{endstring}}}"


class DescendantsHierarchySet(MdxHierarchySet):

    def __init__(self, member: Member, level_or_depth: Union[int, MdxLevelExpression] = None,
                 description_flag: DescFlag = None):
        super(DescendantsHierarchySet, self).__init__(member.dimension, member.hierarchy)
        self.member = member
        self.level_or_depth = level_or_depth
        self.descFlag = DescFlag(description_flag) if description_flag is not None else None

    def to_mdx(self) -> str:
        if isinstance(self.level_or_depth, MdxLevelExpression):
            level_expression = f', {self.level_or_depth.to_mdx()}'
        else:
            level_expression = f",{self.level_or_depth}" if self.level_or_depth is not None else ''

        flag = f", {self.descFlag}" if self.descFlag is not None else ''
        return f"{{DESCENDANTS({self.member.unique_name}{level_expression}{flag})}}"


class RangeHierarchySet(MdxHierarchySet):
    def __init__(self, start_member: Member, end_member: Member):
        super(RangeHierarchySet, self).__init__(start_member.dimension, start_member.hierarchy)
        self._start_member = start_member
        self._end_member = end_member

    def to_mdx(self) -> str:
        return f"{{{self._start_member.unique_name}:{self._end_member.unique_name}}}"


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


class Tm1FilterByElementTypeHierarchySet(MdxHierarchySet):

    def __init__(self, underlying_hierarchy_set: MdxHierarchySet, element_type: Union[ElementType, str]):
        super(Tm1FilterByElementTypeHierarchySet, self).__init__(underlying_hierarchy_set.dimension,
                                                                 underlying_hierarchy_set.hierarchy)
        self.underlying_hierarchy_set = underlying_hierarchy_set
        self.element_type = ElementType(element_type)

    def to_mdx(self) -> str:
        return f"{{FILTER({self.underlying_hierarchy_set.to_mdx()},[{self.dimension}].[{self.hierarchy}]" \
               f".CURRENTMEMBER.PROPERTIES('ELEMENT_TYPE')='{self.element_type.value}')}}"


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
        self.substring = substring.lower() if case_insensitive else substring
        self.operator = operator
        self.position = position
        self.case_insensitive = case_insensitive

    def to_mdx(self) -> str:
        return f"{{FILTER({self.underlying_hierarchy_set.to_mdx()},INSTR({'LCASE(' if self.case_insensitive else ''}" \
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


class HierarchizeSet(MdxHierarchySet):

    def __init__(self, underlying_hierarchy_set: MdxHierarchySet):
        super(HierarchizeSet, self).__init__(underlying_hierarchy_set.dimension,
                                             underlying_hierarchy_set.hierarchy)
        self.underlying_hierarchy_set = underlying_hierarchy_set

    def to_mdx(self) -> str:
        return f"{{HIERARCHIZE({self.underlying_hierarchy_set.to_mdx()})}}"


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

    def __init__(self, underlying_hierarchy_set: MdxHierarchySet, other_hierarchy_set: MdxHierarchySet,
                 allow_duplicates: bool):
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
        self.dimension = dimension.lower()
        self.hierarchy = hierarchy.lower() if hierarchy else self.dimension
        self.attribute = attribute

    def to_mdx(self) -> str:
        return f"{{GENERATE({self.underlying_hierarchy_set.to_mdx()}," \
               f"{{STRTOMEMBER('[{self.dimension}].[{self.hierarchy}].[' + [{self.underlying_hierarchy_set.dimension}].[{self.underlying_hierarchy_set.hierarchy}].CURRENTMEMBER.PROPERTIES(\"{self.attribute}\") + ']')}})}}"


class MultiUnionHierarchySet(MdxHierarchySet):

    def __init__(self, sets: List[MdxHierarchySet], allow_duplicates: bool = False):
        if not sets:
            raise RuntimeError('sets must not be empty')

        super(MultiUnionHierarchySet, self).__init__(
            sets[0].dimension,
            sets[0].hierarchy)

        self.sets = sets
        self.allow_duplicates = allow_duplicates

    def to_mdx(self) -> str:
        if self.allow_duplicates:
            return f"{{{','.join(set_.to_mdx() for set_ in self.sets)}}}"
        else:
            return f"{{{' + '.join(set_.to_mdx() for set_ in self.sets)}}}"


class MdxAxis:
    def __init__(self):
        self.tuples: List[MdxTuple] = list()
        self.dim_sets: List[MdxSet] = list()
        self.non_empty = False

    @staticmethod
    def empty() -> 'MdxAxis':
        return MdxAxis()

    def add_tuple(self, mdx_tuple: MdxTuple):
        if bool(self.dim_sets):
            raise ValueError("Can not add tuple to axis that contains sets")

        self.tuples.append(mdx_tuple)

    def add_set(self, mdx_set: MdxSet):
        if bool(self.tuples):
            raise ValueError("Can not add set to axis that contains tuples")

        if not isinstance(mdx_set, MdxSet):
            raise ValueError("Can not add MDX Tuples to axis using set method")

        self.dim_sets.append(mdx_set)

    def is_empty(self) -> bool:
        return not self.dim_sets and not self.tuples

    def set_non_empty(self, non_empty: bool = True):
        self.non_empty = non_empty

    def to_mdx(self, tm1_ignore_bad_tuples: bool = False, head: int = None, tail: int = None) -> str:
        if self.is_empty():
            return "{}"

        return f"""{"NON EMPTY " if self.non_empty else ""}{"TM1IGNORE_BADTUPLES " if tm1_ignore_bad_tuples else ""}{self.dim_sets_to_mdx(head, tail) if self.dim_sets else self.tuples_to_mdx(head, tail)}"""

    def dim_sets_to_mdx(self, head: int = None, tail: int = None) -> str:
        mdx = " * ".join(dim_set.to_mdx() for dim_set in self.dim_sets)
        if head is not None:
            mdx = f"{{HEAD({mdx}, {head})}}"
        if tail is not None:
            mdx = f"{{TAIL({mdx}, {tail})}}"

        return mdx

    def tuples_to_mdx(self, head: int = None, tail: int = None) -> str:
        mdx = f"{{{','.join(tupl.to_mdx() for tupl in self.tuples)}}}"
        if head is not None:
            mdx = f"{{HEAD({mdx}, {head})}}"
        if tail is not None:
            mdx = f"{{TAIL({mdx}, {tail})}}"

        return mdx


class MdxBuilder:
    def __init__(self, cube: str):
        self.cube = normalize(cube)
        self.axes = {0: MdxAxis.empty()}
        self._where = MdxTuple.empty()
        # dimension properties by axis
        self.axes_properties = {0: MdxPropertiesTuple.empty()}
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

    def _add_tuple_to_axis(self, axis: MdxAxis, *args: Union[str, Member, MdxTuple]) -> 'MdxBuilder':
        if isinstance(args[0], MdxTuple):
            mdx_tuple = args[0]
        else:
            mdx_tuple = MdxTuple.of(*args)
        axis.add_tuple(mdx_tuple)
        return self

    def add_member_tuple_to_axis(self, axis: int, *args: Union[str, Member, MdxTuple]) -> 'MdxBuilder':
        if axis not in self.axes:
            self.axes[axis] = MdxAxis.empty()
        return self._add_tuple_to_axis(self.axes[axis], *args)

    def add_member_tuple_to_columns(self, *args: Union[str, Member, MdxTuple]) -> 'MdxBuilder':
        return self.add_member_tuple_to_axis(0, *args)

    def add_member_tuple_to_rows(self, *args: Union[str, Member, MdxTuple]) -> 'MdxBuilder':
        return self.add_member_tuple_to_axis(1, *args)

    def add_hierarchy_set_to_row_axis(self, mdx_hierarchy_set: MdxHierarchySet) -> 'MdxBuilder':
        return self.add_hierarchy_set_to_axis(1, mdx_hierarchy_set)

    def add_hierarchy_set_to_column_axis(self, mdx_hierarchy_set: MdxHierarchySet) -> 'MdxBuilder':
        return self.add_hierarchy_set_to_axis(0, mdx_hierarchy_set)

    def add_set_to_row_axis(self, mdx_set: MdxSet) -> 'MdxBuilder':
        return self.add_set_to_axis(1, mdx_set)

    def add_set_to_column_axis(self, mdx_set: MdxSet) -> 'MdxBuilder':
        return self.add_set_to_axis(0, mdx_set)

    def add_hierarchy_set_to_axis(self, axis: int, mdx_hierarchy_set: MdxHierarchySet) -> 'MdxBuilder':
        return self.add_set_to_axis(axis, mdx_hierarchy_set)

    def add_set_to_axis(self, axis: int, mdx_set: MdxSet) -> 'MdxBuilder':
        if axis not in self.axes:
            self.axes[axis] = MdxAxis.empty()

        self.axes[axis].add_set(mdx_set)
        return self

    def add_empty_set_to_axis(self, axis: int):
        if axis in self.axes:
            raise ValueError(f"axis: '{axis}' must be empty")

        hierarchy_set = MdxHierarchySet.from_str("", "", "{}")
        return self.add_hierarchy_set_to_axis(axis, hierarchy_set)

    def add_member_to_where(self, member: Union[str, Member]) -> 'MdxBuilder':
        self._where.add_member(member)
        return self

    def add_member_to_properties(self, axis: int, member: Union[str, DimensionProperty]) -> 'MdxBuilder':
        if axis in self.axes_properties:
            self.axes_properties[axis].add_member(member)
        else:
            self.axes_properties[axis] = MdxPropertiesTuple([member])
        return self

    def where(self, *args: Union[str, Member]) -> 'MdxBuilder':
        for member in args:
            if isinstance(member, str):
                member = Member.of(member)
            if not isinstance(member, Member):
                raise ValueError(f"Argument '{member}' must be of type str or Member")
            self.add_member_to_where(member)
        return self

    def add_properties_to_row_axis(self, *args: Union[str, DimensionProperty]) -> 'MdxBuilder':
        return self.add_properties(1, *args)

    def add_properties_to_column_axis(self, *args: Union[str, DimensionProperty]) -> 'MdxBuilder':
        return self.add_properties(0, *args)

    def add_properties(self, axis: int, *args: Union[str, DimensionProperty]) -> 'MdxBuilder':
        for member in args:
            if isinstance(member, str):
                member = DimensionProperty.of(member)

            if not isinstance(member, DimensionProperty):
                raise ValueError(f"Argument '{member}' must be of type str or DimensionProperty")

            self.add_member_to_properties(axis, member)

        return self

    def _axis_mdx(self, position: int, head: int = None, tail: int = None, skip_dimension_properties=False):
        axis = self.axes[position]
        axis_properties = self.axes_properties.get(position, MdxPropertiesTuple.empty())
        if axis.is_empty():
            return ""

        if skip_dimension_properties:
            return " ".join([
                axis.to_mdx(self._tm1_ignore_bad_tuples, head, tail),
                f"ON {position}"
            ])

        return " ".join([
            axis.to_mdx(self._tm1_ignore_bad_tuples, head, tail),
            "DIMENSION PROPERTIES",
            "MEMBER_NAME" if axis_properties.is_empty() else axis_properties.to_mdx(),
            f"ON {position}"
        ])

    def to_mdx(self, head_columns: int = None, head_rows: int = None, tail_columns: int = None, tail_rows: int = None,
               skip_dimension_properties: bool = False) -> str:
        mdx_with = "WITH\r\n" + "\r\n".join(
            calculated_member.to_mdx()
            for calculated_member
            in self.calculated_members) + "\r\n"

        head_by_axis_position = {0: head_columns, 1: head_rows}
        tail_by_axis_position = {0: tail_columns, 1: tail_rows}

        mdx_axes = ",\r\n".join(
            self._axis_mdx(
                position,
                # default for head, tail is False for axes beyond rows and columns
                head=head_by_axis_position.get(position, None),
                tail=tail_by_axis_position.get(position, None),
                skip_dimension_properties=skip_dimension_properties)
            for position
            in self.axes)

        mdx_where = "\r\nWHERE " + self._where.to_mdx() if not self._where.is_empty() else ""

        return f"""{mdx_with if self.calculated_members else ""}SELECT\r\n{mdx_axes}\r\nFROM [{self.cube}]{mdx_where}"""

    def to_clipboard(self):
        mdx = self.to_mdx()
        mdx = mdx.replace('\r\n', ' ')
        command = 'echo | set /p nul="' + mdx + '"| clip'
        os.system(command)
        print(mdx)
