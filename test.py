import unittest

import pytest

from mdxpy import DimensionProperty, Member, MdxTuple, MdxHierarchySet, normalize, MdxBuilder, CalculatedMember, MdxSet, \
    Order, ElementType, MdxLevelExpression


class Test(unittest.TestCase):

    def setUp(self) -> None:
        Member.SHORT_NOTATION = False

    def test_normalize_simple(self):
        value = normalize("ele ment")
        self.assertEqual(value, "element")

    def test_normalize_escape_bracket(self):
        value = normalize("ele me]nt")
        self.assertEqual(value, "eleme]]nt")

    def test_member_of_one_arg(self):
        dimension_element = Member.of("[Dimension].[Element]")
        self.assertEqual(dimension_element.dimension, "Dimension")
        self.assertEqual(dimension_element.hierarchy, "Dimension")
        self.assertEqual(dimension_element.element, "Element")

    def test_member_of_one_arg_with_hierarchy(self):
        dimension_element = Member.of("[Dimension].[Hierarchy].[Element]")
        self.assertEqual(dimension_element.dimension, "Dimension")
        self.assertEqual(dimension_element.hierarchy, "Hierarchy")
        self.assertEqual(dimension_element.element, "Element")

    def test_member_of_two_args(self):
        dimension_element = Member.of("Dimension", "Element")
        self.assertEqual(dimension_element.dimension, "Dimension")
        self.assertEqual(dimension_element.hierarchy, "Dimension")
        self.assertEqual(dimension_element.element, "Element")

    def test_member_of_three_arguments(self):
        dimension_element = Member.of("Dimension", "Hierarchy", "Element")
        self.assertEqual(dimension_element.dimension, "Dimension")
        self.assertEqual(dimension_element.hierarchy, "Hierarchy")
        self.assertEqual(dimension_element.element, "Element")

    def test_member_of_error(self):
        with pytest.raises(ValueError):
            Member.of("Dim")

    def test_member_unique_name_without_hierarchy(self):
        element = Member.of("Dim", "Elem")
        self.assertEqual(element.unique_name, "[dim].[dim].[elem]")

    def test_member_unique_name_with_hierarchy(self):
        element = Member.of("Dim", "Hier", "Elem")
        self.assertEqual(element.unique_name, "[dim].[hier].[elem]")

    def test_calculated_member_avg(self):
        calculated_member = CalculatedMember.avg(
            dimension="Period",
            hierarchy="Period",
            element="AVG 2016",
            cube="Cube",
            mdx_set=MdxHierarchySet.children(Member.of("Period", "2016")),
            mdx_tuple=MdxTuple.of(Member.of("Dimension1", "Element1"), Member.of("Dimension2", "Element2")))

        self.assertEqual(
            calculated_member.to_mdx(),
            "MEMBER [period].[period].[avg2016] AS AVG({[period].[period].[2016].CHILDREN},[cube]."
            "([dimension1].[dimension1].[element1],[dimension2].[dimension2].[element2]))")

    def test_calculated_member_sum(self):
        calculated_member = CalculatedMember.sum(
            dimension="Period",
            hierarchy="Period",
            element="SUM 2016",
            cube="Cube",
            mdx_set=MdxHierarchySet.children(Member.of("Period", "2016")),
            mdx_tuple=MdxTuple.of(Member.of("Dimension1", "Element1"), Member.of("Dimension2", "Element2")))

        self.assertEqual(
            calculated_member.to_mdx(),
            "MEMBER [period].[period].[sum2016] AS SUM({[period].[period].[2016].CHILDREN},[cube]."
            "([dimension1].[dimension1].[element1],[dimension2].[dimension2].[element2]))")

    def test_calculated_member_lookup_attribute(self):
        calculated_member = CalculatedMember.lookup_attribute(
            dimension="Period",
            hierarchy="Period",
            element="VersionAttribute1",
            attribute_dimension="Version",
            attribute="Attribute1")

        self.assertEqual(
            calculated_member.to_mdx(),
            "MEMBER [period].[period].[versionattribute1] AS [}ELEMENTATTRIBUTES_version]."
            "([}ELEMENTATTRIBUTES_version].[attribute1])")

    def test_calculated_member_lookup(self):
        calculated_member = CalculatedMember.lookup(
            "Period",
            "Period",
            "VersionAttribute1",
            cube="}ELEMENTATTRIBUTES_version",
            mdx_tuple=MdxTuple.of(Member.of("}ELEMENTATTRIBUTES_version", "Attribute1")))

        self.assertEqual(
            calculated_member.to_mdx(),
            "MEMBER [period].[period].[versionattribute1] AS [}elementattributes_version]."
            "([}elementattributes_version].[}elementattributes_version].[attribute1])")

    def test_mdx_tuple_empty(self):
        tupl = MdxTuple.empty()
        self.assertEqual(tupl.members, list())

    def test_mdx_tuple_create(self):
        tupl = MdxTuple.of(
            Member.of("Dimension1", "Hierarchy1", "Element1"),
            Member.of("Dimension2", "Hierarchy2", "Element2"))

        self.assertEqual(len(tupl), 2)
        self.assertEqual(tupl.members[0], Member.of("Dimension1", "Hierarchy1", "Element1"))
        self.assertEqual(tupl.members[1], Member.of("Dimension2", "Hierarchy2", "Element2"))

    def test_mdx_tuple_add_element(self):
        tupl = MdxTuple.of(Member.of("Dimension1", "Hierarchy1", "Element1"))
        tupl.add_member(Member.of("Dimension2", "Hierarchy2", "Element2"))

        self.assertEqual(len(tupl), 2)
        self.assertEqual(tupl.members[0], Member.of("Dimension1", "Hierarchy1", "Element1"))
        self.assertEqual(tupl.members[1], Member.of("Dimension2", "Hierarchy2", "Element2"))

    def test_mdx_hierarchy_set_tm1_subset_all(self):
        hierarchy_set = MdxHierarchySet.tm1_subset_all("Dimension")
        self.assertEqual(
            "{TM1SUBSETALL([dimension].[dimension])}",
            hierarchy_set.to_mdx())

    def test_mdx_hierarchy_set_all_members(self):
        hierarchy_set = MdxHierarchySet.all_members("Dimension", "Hierarchy")
        self.assertEqual(
            "{[dimension].[hierarchy].MEMBERS}",
            hierarchy_set.to_mdx())

    def test_mdx_hierarchy_set_tm1_subset_to_set(self):
        hierarchy_set = MdxHierarchySet.tm1_subset_to_set("Dimension", "Hierarchy", "Default")
        self.assertEqual(
            '{TM1SUBSETTOSET([dimension].[hierarchy],"Default")}',
            hierarchy_set.to_mdx())

    def test_mdx_hierarchy_set_tm1_dimension_subset_to_set(self):
        hierarchy_set = MdxHierarchySet.tm1_dimension_subset_to_set("Dimension", "Default")
        self.assertEqual(
            '{TM1SUBSETTOSET([dimension].[dimension],"Default")}',
            hierarchy_set.to_mdx())

    def test_mdx_hierarchy_set_all_consolidations(self):
        hierarchy_set = MdxHierarchySet.all_consolidations("Dimension")
        self.assertEqual(
            "{EXCEPT("
            "{TM1SUBSETALL([dimension].[dimension])},"
            "{TM1FILTERBYLEVEL({TM1SUBSETALL([dimension].[dimension])},0)})}",
            hierarchy_set.to_mdx())

    def test_mdx_hierarchy_set_all_leaves(self):
        hierarchy_set = MdxHierarchySet.all_leaves("Dimension")
        self.assertEqual("{TM1FILTERBYLEVEL({TM1SUBSETALL([dimension].[dimension])},0)}", hierarchy_set.to_mdx())

    def test_mdx_hierarchy_set_default_member(self):
        hierarchy_set = MdxHierarchySet.default_member("Dimension")
        self.assertEqual("{[dimension].[dimension].DEFAULTMEMBER}", hierarchy_set.to_mdx())

    def test_mdx_hierarchy_set_elements(self):
        hierarchy_set = MdxHierarchySet.members(
            [Member.of("Dimension", "element1"), Member.of("Dimension", "element2")])
        self.assertEqual(
            "{[dimension].[dimension].[element1],[dimension].[dimension].[element2]}",
            hierarchy_set.to_mdx())

    def test_mdx_set_unions_no_duplicates(self):
        hierarchy_set = MdxSet.unions([
            MdxHierarchySet.children(Member.of("Dimension", "element1")),
            MdxHierarchySet.member(Member.of("Dimension", "element2")),
            MdxHierarchySet.member(Member.of("Dimension", "element3"))
        ])

        self.assertEqual(
            "{{[dimension].[dimension].[element1].CHILDREN}"
            " + {[dimension].[dimension].[element2]}"
            " + {[dimension].[dimension].[element3]}}",
            hierarchy_set.to_mdx())

    def test_mdx_set_unions_allow_duplicates(self):
        hierarchy_set = MdxSet.unions([
            MdxHierarchySet.children(Member.of("Dimension", "element1")),
            MdxHierarchySet.member(Member.of("Dimension", "element2")),
            MdxHierarchySet.member(Member.of("Dimension", "element3"))
        ], True)

        self.assertEqual(
            "{{[dimension].[dimension].[element1].CHILDREN},"
            "{[dimension].[dimension].[element2]},"
            "{[dimension].[dimension].[element3]}}",
            hierarchy_set.to_mdx())

    def test_mdx_set_cross_joins(self):
        mdx_set = MdxSet.cross_joins([
            MdxHierarchySet.children(Member.of("Dimension", "element1")),
            MdxHierarchySet.member(Member.of("Dimension", "element2")),
            MdxHierarchySet.member(Member.of("Dimension", "element3"))
        ])

        self.assertEqual(
            "{{[dimension].[dimension].[element1].CHILDREN}"
            " * {[dimension].[dimension].[element2]}"
            " * {[dimension].[dimension].[element3]}}",
            mdx_set.to_mdx())


    def test_mdx_set_tuples(self):
        mdx_set = MdxSet.tuples([
            MdxTuple([Member.of("dimension1", "element1"), Member.of("dimension2", "element3")]),
            MdxTuple([Member.of("dimension1", "element2"), Member.of("dimension2", "element2")]),
            MdxTuple([Member.of("dimension1", "element3"), Member.of("dimension2", "element1")])
        ])

        self.assertEqual(
            "{ ([dimension1].[dimension1].[element1],[dimension2].[dimension2].[element3]),"
            "([dimension1].[dimension1].[element2],[dimension2].[dimension2].[element2]),"
            "([dimension1].[dimension1].[element3],[dimension2].[dimension2].[element1]) }",
            mdx_set.to_mdx())

    def test_mdx_hierarchy_set_parent(self):
        hierarchy_set = MdxHierarchySet.parent(Member.of("Dimension", "Element"))

        self.assertEqual(
            "{[dimension].[dimension].[element].PARENT}",
            hierarchy_set.to_mdx())

    def test_mdx_hierarchy_set_first_child(self):
        hierarchy_set = MdxHierarchySet.first_child(Member.of("Dimension", "Element"))

        self.assertEqual(
            "{[dimension].[dimension].[element].FIRSTCHILD}",
            hierarchy_set.to_mdx())

    def test_mdx_hierarchy_set_last_child(self):
        hierarchy_set = MdxHierarchySet.last_child(Member.of("Dimension", "Element"))

        self.assertEqual(
            "{[dimension].[dimension].[element].LASTCHILD}",
            hierarchy_set.to_mdx())

    def test_mdx_hierarchy_set_children(self):
        hierarchy_set = MdxHierarchySet.children(Member.of("Dimension", "Element"))

        self.assertEqual(
            "{[dimension].[dimension].[element].CHILDREN}",
            hierarchy_set.to_mdx())

    def test_mdx_hierarchy_set_ancestors(self):
        hierarchy_set = MdxHierarchySet.ancestors(Member.of("Dimension", "Element"))

        self.assertEqual(
            "{[dimension].[dimension].[element].ANCESTORS}",
            hierarchy_set.to_mdx())

    def test_mdx_hierarchy_set_ancestor(self):
        hierarchy_set = MdxHierarchySet.ancestor(Member.of("Dimension", "Element"), 1)

        self.assertEqual(
            "{ANCESTOR([dimension].[dimension].[element],1)}",
            hierarchy_set.to_mdx())

    def test_mdx_hierarchy_set_drill_down_level(self):
        hierarchy_set = MdxHierarchySet.drill_down_level(Member.of("Dimension", "Element"), level=1)

        self.assertEqual(
            "{DRILLDOWNLEVEL({[dimension].[dimension].[element]})}",
            hierarchy_set.to_mdx())

        hierarchy_set = MdxHierarchySet.drill_down_level(Member.of("Dimension", "Element"), level=3)

        self.assertEqual(
            "{DRILLDOWNLEVEL(DRILLDOWNLEVEL(DRILLDOWNLEVEL({[dimension].[dimension].[element]})))}",
            hierarchy_set.to_mdx())


    def test_mdx_hierarchy_set_tm1_drill_down_member_all_recursive(self):
        hierarchy_set = MdxHierarchySet.members([Member.of("dimension", "element")]).tm1_drill_down_member(
            recursive=True)

        self.assertEqual(
            "{TM1DRILLDOWNMEMBER({[dimension].[dimension].[element]}, ALL, RECURSIVE)}",
            hierarchy_set.to_mdx())

    def test_mdx_hierarchy_set_tm1_drill_down_member_set_recursive(self):
        hierarchy_set = MdxHierarchySet.members([Member.of("dimension", "element")]).tm1_drill_down_member(
            other_set=MdxHierarchySet.members([Member.of("dimension", "element")]),
            recursive=True)
        self.assertEqual(
            "{TM1DRILLDOWNMEMBER({[dimension].[dimension].[element]}, {[dimension].[dimension].[element]}, RECURSIVE)}",
            hierarchy_set.to_mdx())

    def test_mdx_hierarchy_set_tm1_drill_down_member_all(self):
        hierarchy_set = MdxHierarchySet.members([Member.of("dimension", "element")]).tm1_drill_down_member(
            recursive=False)

        self.assertEqual(
            "{TM1DRILLDOWNMEMBER({[dimension].[dimension].[element]}, ALL)}",
            hierarchy_set.to_mdx())

    def test_mdx_hierarchy_set_tm1_drill_down_member_set(self):
        hierarchy_set = MdxHierarchySet.members([Member.of("dimension", "element")]).tm1_drill_down_member(
            other_set=MdxHierarchySet.members([Member.of("dimension", "element")]), recursive=False)
        self.assertEqual(
            "{TM1DRILLDOWNMEMBER({[dimension].[dimension].[element]}, {[dimension].[dimension].[element]})}",
            hierarchy_set.to_mdx())

    def test_mdx_hierarchy_set_from_str(self):
        hierarchy_set = MdxHierarchySet.from_str(
            dimension="Dimension",
            hierarchy="Hierarchy",
            mdx="{[dimension].[hierarchy].MEMBERS}")

        self.assertEqual(hierarchy_set.to_mdx(), "{[dimension].[hierarchy].MEMBERS}")

    def test_mdx_hierarchy_set_from_str_with_other(self):
        hierarchy_set = MdxHierarchySet.from_str(
            dimension="Dimension",
            hierarchy="Hierarchy",
            mdx="{[dimension].[hierarchy].MEMBERS}").filter_by_attribute("Attribute1", ["Value1"])

        self.assertEqual(
            hierarchy_set.to_mdx(),
            '{FILTER({[dimension].[hierarchy].MEMBERS},'
            '[}ELEMENTATTRIBUTES_dimension].([}ELEMENTATTRIBUTES_dimension].[Attribute1])="Value1")}')

    def test_mdx_filter_by_attribute_single_string(self):
        hierarchy_set = MdxHierarchySet.tm1_subset_all("Dimension").filter_by_attribute("Attribute1", ["Value1"])
        self.assertEqual(
            "{FILTER({TM1SUBSETALL([dimension].[dimension])},"
            '[}ELEMENTATTRIBUTES_dimension].([}ELEMENTATTRIBUTES_dimension].[Attribute1])="Value1")}',
            hierarchy_set.to_mdx())

    def test_mdx_filter_by_attribute_single_numeric(self):
        hierarchy_set = MdxHierarchySet.tm1_subset_all("Dimension").filter_by_attribute("Attribute1", [1])

        self.assertEqual(
            "{FILTER({TM1SUBSETALL([dimension].[dimension])},"
            "[}ELEMENTATTRIBUTES_dimension].([}ELEMENTATTRIBUTES_dimension].[Attribute1])=1)}",
            hierarchy_set.to_mdx())

    def test_mdx_filter_by_attribute_multiple(self):
        hierarchy_set = MdxHierarchySet.tm1_subset_all("Dimension").filter_by_attribute("Attribute1",
                                                                                        ["Value1", 1, 2.0])

        self.assertEqual(
            '{FILTER({TM1SUBSETALL([dimension].[dimension])},'
            '[}ELEMENTATTRIBUTES_dimension].([}ELEMENTATTRIBUTES_dimension].[Attribute1])="Value1" OR '
            '[}ELEMENTATTRIBUTES_dimension].([}ELEMENTATTRIBUTES_dimension].[Attribute1])=1 OR '
            '[}ELEMENTATTRIBUTES_dimension].([}ELEMENTATTRIBUTES_dimension].[Attribute1])=2.0)}',
            hierarchy_set.to_mdx())

    def test_mdx_hierarchy_set_filter_by_wildcard(self):
        hierarchy_set = MdxHierarchySet.all_members("Dimension", "Hierarchy").filter_by_pattern("2011*")

        self.assertEqual(
            "{TM1FILTERBYPATTERN({[dimension].[hierarchy].MEMBERS},'2011*')}",
            hierarchy_set.to_mdx())

    def test_mdx_hierarchy_set_filter_by_level(self):
        hierarchy_set = MdxHierarchySet.all_members("Dimension", "Hierarchy").filter_by_level(0)

        self.assertEqual(
            "{TM1FILTERBYLEVEL({[dimension].[hierarchy].MEMBERS},0)}",
            hierarchy_set.to_mdx())

    def test_mdx_hierarchy_set_filter_by_element_type(self):
        hierarchy_set = MdxHierarchySet.all_members("Dimension", "Hierarchy").filter_by_element_type(
            ElementType.NUMERIC)

        self.assertEqual(
            "{FILTER({[dimension].[hierarchy].MEMBERS},"
            "[dimension].[hierarchy].CURRENTMEMBER.PROPERTIES('ELEMENT_TYPE')='1')}",
            hierarchy_set.to_mdx())

    def test_mdx_hierarchy_set_filter_by_element_type_str(self):
        hierarchy_set = MdxHierarchySet.all_members("Dimension", "Hierarchy").filter_by_element_type("Numeric")

        self.assertEqual(
            "{FILTER({[dimension].[hierarchy].MEMBERS},"
            "[dimension].[hierarchy].CURRENTMEMBER.PROPERTIES('ELEMENT_TYPE')='1')}",
            hierarchy_set.to_mdx())

    def test_mdx_hierarchy_set_filter_by_cell_value_numeric(self):
        hierarchy_set = MdxHierarchySet.all_members("Dimension1", "Hierarchy1").filter_by_cell_value(
            cube="Cube",
            mdx_tuple=MdxTuple.of(
                Member.of("Dimension2", "Hierarchy2", "ElementA"),
                Member.of("Dimension3", "Hierarchy3", "ElementB")),
            operator="=",
            value=1)

        self.assertEqual(
            "{FILTER({[dimension1].[hierarchy1].MEMBERS},"
            "[cube].([dimension2].[hierarchy2].[elementa],[dimension3].[hierarchy3].[elementb])=1)}",
            hierarchy_set.to_mdx())

    def test_mdx_hierarchy_set_filter_by_cell_value_string(self):
        hierarchy_set = MdxHierarchySet.all_members("Dimension1", "Hierarchy1").filter_by_cell_value(
            cube="Cube",
            mdx_tuple=MdxTuple.of(
                Member.of("Dimension2", "ElementA"),
                Member.of("Dimension3", "ElementB")),
            operator="=",
            value='ABC')

        self.assertEqual(
            "{FILTER({[dimension1].[hierarchy1].MEMBERS},"
            "[cube].([dimension2].[dimension2].[elementa],[dimension3].[dimension3].[elementb])='ABC')}",
            hierarchy_set.to_mdx())

    def test_mdx_hierarchy_set_tm1_sort_asc(self):
        hierarchy_set = MdxHierarchySet.tm1_subset_all("Dimension", "Hierarchy").tm1_sort(True)

        self.assertEqual(
            "{TM1SORT({TM1SUBSETALL([dimension].[hierarchy])},ASC)}",
            hierarchy_set.to_mdx())

    def test_mdx_hierarchy_set_tm1_sort_desc(self):
        hierarchy_set = MdxHierarchySet.tm1_subset_all("Dimension").tm1_sort(False)

        self.assertEqual(
            "{TM1SORT({TM1SUBSETALL([dimension].[dimension])},DESC)}",
            hierarchy_set.to_mdx())

    def test_mdx_hierarchy_set_hierarchize(self):
        hierarchy_set = MdxHierarchySet.tm1_subset_all("Dimension").hierarchize()

        self.assertEqual(
            "{HIERARCHIZE({TM1SUBSETALL([dimension].[dimension])})}",
            hierarchy_set.to_mdx())

    def test_mdx_hierarchy_descendants(self):
        member = Member.of('Dimension', 'Hierarchy', 'Member1')
        hierarchy_set = MdxHierarchySet.descendants(member)
        self.assertEqual("{DESCENDANTS([dimension].[hierarchy].[member1])}", hierarchy_set.to_mdx())

    def test_mdx_hierarchy_descendants_with_flag(self):
        member = Member.of('Dimension', 'Hierarchy', 'Member1')
        hierarchy_set = MdxHierarchySet.descendants(member, desc_flag='SELF_AND_BEFORE')
        self.assertEqual("{DESCENDANTS([dimension].[hierarchy].[member1], SELF_AND_BEFORE)}", hierarchy_set.to_mdx())

    def test_mdx_hierarchy_descendants_with_flag_and_level_name(self):
        member = Member.of('Dimension', 'Hierarchy', 'Member1')
        hierarchy_set = MdxHierarchySet.descendants(member,
                                                    MdxLevelExpression.level_name('NamedLevel',
                                                                                  'Dimension',
                                                                                  'Hierarchy'),
                                                    desc_flag='SELF_AND_BEFORE')
        self.assertEqual("{DESCENDANTS([dimension].[hierarchy].[member1], "
                         "[dimension].[hierarchy].LEVELS('NamedLevel'), "
                         "SELF_AND_BEFORE)}",
                         hierarchy_set.to_mdx())

    def test_mdx_hierarchy_descendants_with_flag_and_level_number(self):
        member = Member.of('Dimension', 'Hierarchy', 'Member1')
        hierarchy_set = MdxHierarchySet.descendants(member,
                                                    MdxLevelExpression.level_number(2,
                                                                                    'Dimension',
                                                                                    'Hierarchy'),
                                                    desc_flag='SELF_AND_BEFORE')
        self.assertEqual("{DESCENDANTS([dimension].[hierarchy].[member1], "
                         "[dimension].[hierarchy].LEVELS(2), "
                         "SELF_AND_BEFORE)}",
                         hierarchy_set.to_mdx())

    def test_mdx_hierarchy_descendants_with_flag_and_member_level(self):
        member = Member.of('Dimension', 'Hierarchy', 'Member1')
        hierarchy_set = MdxHierarchySet.descendants(member,
                                                    MdxLevelExpression.member_level(member),
                                                    desc_flag='SELF_AND_BEFORE')
        self.assertEqual("{DESCENDANTS([dimension].[hierarchy].[member1], "
                         "[dimension].[hierarchy].[member1].LEVEL, "
                         "SELF_AND_BEFORE)}",
                         hierarchy_set.to_mdx())

    def test_mdx_hierarchy_set_range(self):
        member1 = Member.of('Dimension', 'Hierarchy', 'Member1')
        member2 = Member.of('Dimension', 'Hierarchy', 'Member2')

        hierarchy_set = MdxHierarchySet.range(member1, member2)

        self.assertEqual("{[dimension].[hierarchy].[member1]:[dimension].[hierarchy].[member2]}",
                         hierarchy_set.to_mdx())

    def test_mdx_hierarchy_set_head(self):
        hierarchy_set = MdxHierarchySet.tm1_subset_all("Dimension").head(10)

        self.assertEqual(
            "{HEAD({TM1SUBSETALL([dimension].[dimension])},10)}",
            hierarchy_set.to_mdx())

    def test_mdx_hierarchy_set_tail(self):
        hierarchy_set = MdxHierarchySet.tm1_subset_all("Dimension").tail(10)

        self.assertEqual(
            "{TAIL({TM1SUBSETALL([dimension].[dimension])},10)}",
            hierarchy_set.to_mdx())

    def test_mdx_hierarchy_set_subset(self):
        hierarchy_set = MdxHierarchySet.tm1_subset_all("Dimension").subset(1, 3)

        self.assertEqual(
            "{SUBSET({TM1SUBSETALL([dimension].[dimension])},1,3)}",
            hierarchy_set.to_mdx())

    def test_mdx_hierarchy_set_top_count(self):
        hierarchy_set = MdxHierarchySet \
            .tm1_subset_all("Dimension") \
            .top_count("cube", MdxTuple.of(Member.of("dimension2", "element2"), Member.of("dimension3", "element3")),
                       10)

        self.assertEqual(
            "{TOPCOUNT({TM1SUBSETALL([dimension].[dimension])},"
            "10,"
            "[cube].([dimension2].[dimension2].[element2],[dimension3].[dimension3].[element3]))}",
            hierarchy_set.to_mdx())

    def test_mdx_hierarchy_set_bottom_count(self):
        hierarchy_set = MdxHierarchySet \
            .tm1_subset_all("Dimension") \
            .bottom_count("cube", MdxTuple.of(Member.of("dimension2", "element2"), Member.of("dimension3", "element3")),
                          10)

        self.assertEqual(
            "{BOTTOMCOUNT({TM1SUBSETALL([dimension].[dimension])},"
            "10,"
            "[cube].([dimension2].[dimension2].[element2],[dimension3].[dimension3].[element3]))}",
            hierarchy_set.to_mdx())

    def test_mdx_hierarchy_set_union(self):
        hierarchy_set = MdxHierarchySet.member(Member.of("dimension", "element1")). \
            union(MdxHierarchySet.member(Member.of("dimension", "element2")))

        self.assertEqual(
            "{UNION({[dimension].[dimension].[element1]},{[dimension].[dimension].[element2]})}",
            hierarchy_set.to_mdx())

    def test_mdx_hierarchy_set_intersect(self):
        hierarchy_set = MdxHierarchySet.member(Member.of("dimension", "element1")). \
            intersect(MdxHierarchySet.member(Member.of("dimension", "element2")))

        self.assertEqual(
            "{INTERSECT({[dimension].[dimension].[element1]},{[dimension].[dimension].[element2]})}",
            hierarchy_set.to_mdx())

    def test_mdx_hierarchy_set_except(self):
        hierarchy_set = MdxHierarchySet.member(Member.of("dimension", "element1")). \
            except_(MdxHierarchySet.member(Member.of("dimension", "element2")))

        self.assertEqual(
            "{EXCEPT({[dimension].[dimension].[element1]},{[dimension].[dimension].[element2]})}",
            hierarchy_set.to_mdx())

    def test_mdx_hierarchy_set_order(self):
        hierarchy_set = MdxHierarchySet.all_members("Dimension1", "Hierarchy1").order(
            cube="Cube",
            mdx_tuple=MdxTuple.of(
                Member.of("Dimension2", "Hierarchy2", "ElementA"),
                Member.of("Dimension3", "Hierarchy3", "ElementB")))

        self.assertEqual(
            "{ORDER({[dimension1].[hierarchy1].MEMBERS},"
            "[cube].([dimension2].[hierarchy2].[elementa],[dimension3].[hierarchy3].[elementb]),BASC)}",
            hierarchy_set.to_mdx())

    def test_mdx_hierarchy_set_order_desc(self):
        hierarchy_set = MdxHierarchySet.all_members("Dimension1", "Hierarchy1").order(
            cube="Cube",
            mdx_tuple=MdxTuple.of(
                Member.of("Dimension2", "Hierarchy2", "ElementA"),
                Member.of("Dimension3", "Hierarchy3", "ElementB")),
            order=Order.DESC)

        self.assertEqual(
            "{ORDER({[dimension1].[hierarchy1].MEMBERS},"
            "[cube].([dimension2].[hierarchy2].[elementa],[dimension3].[hierarchy3].[elementb]),DESC)}",
            hierarchy_set.to_mdx())

    def test_mdx_hierarchy_set_order_desc_str(self):
        hierarchy_set = MdxHierarchySet.all_members("Dimension1", "Hierarchy1").order(
            cube="Cube",
            mdx_tuple=MdxTuple.of(
                Member.of("Dimension2", "Hierarchy2", "ElementA"),
                Member.of("Dimension3", "Hierarchy3", "ElementB")),
            order="DESC")

        self.assertEqual(
            "{ORDER({[dimension1].[hierarchy1].MEMBERS},"
            "[cube].([dimension2].[hierarchy2].[elementa],[dimension3].[hierarchy3].[elementb]),DESC)}",
            hierarchy_set.to_mdx())

    def test_mdx_hierarchy_set_order_by_attribute(self):
        hierarchy_set = MdxHierarchySet.all_members("Dimension1", "Hierarchy1").order_by_attribute(
            attribute_name="Attribute1",
            order='asc')

        self.assertEqual(
            '{ORDER({[dimension1].[hierarchy1].MEMBERS},'
            '[dimension1].[hierarchy1].CURRENTMEMBER.PROPERTIES("attribute1"), ASC)}',
            hierarchy_set.to_mdx())

    def test_mdx_hierarchy_set_generate_attribute_to_member(self):
        hierarchy_set = MdxHierarchySet.all_leaves("Store").generate_attribute_to_member(
            attribute="Manager",
            dimension="Manager")

        self.assertEqual(hierarchy_set.dimension, "manager")

        self.assertEqual(
            "{GENERATE("
            "{TM1FILTERBYLEVEL({TM1SUBSETALL([store].[store])},0)},"
            "{STRTOMEMBER('[manager].[manager].[' + [store].[store].CURRENTMEMBER.PROPERTIES(\"Manager\") + ']')})}",
            hierarchy_set.to_mdx())

    def test_mdx_hierarchy_set_unions_allow_duplicates(self):
        hierarchy_set = MdxSet.unions([
            MdxHierarchySet.children(Member.of("Dimension", "element1")),
            MdxHierarchySet.member(Member.of("Dimension", "element2")),
            MdxHierarchySet.member(Member.of("Dimension", "element3"))
        ], True)

        self.assertEqual(
            "{{[dimension].[dimension].[element1].CHILDREN},"
            "{[dimension].[dimension].[element2]},"
            "{[dimension].[dimension].[element3]}}",
            hierarchy_set.to_mdx())

    def test_mdx_builder_simple(self):
        mdx = MdxBuilder.from_cube("cube") \
            .rows_non_empty() \
            .add_hierarchy_set_to_row_axis(MdxHierarchySet.all_leaves("Dim1")) \
            .columns_non_empty() \
            .add_hierarchy_set_to_column_axis(MdxHierarchySet.member(Member.of("Dim2", "Elem2"))) \
            .where(Member.of("Dim3", "Elem3"), Member.of("Dim4", "Elem4")) \
            .to_mdx()

        self.assertEqual(
            "SELECT\r\n"
            "NON EMPTY {[dim2].[dim2].[elem2]} DIMENSION PROPERTIES MEMBER_NAME ON 0,\r\n"
            "NON EMPTY {TM1FILTERBYLEVEL({TM1SUBSETALL([dim1].[dim1])},0)} DIMENSION PROPERTIES MEMBER_NAME ON 1\r\n"
            "FROM [cube]\r\n"
            "WHERE ([dim3].[dim3].[elem3],[dim4].[dim4].[elem4])",
            mdx)

    def test_mdx_builder_simple_properties(self):
        mdx = MdxBuilder.from_cube("cube") \
            .rows_non_empty() \
            .add_hierarchy_set_to_row_axis(MdxHierarchySet.all_leaves("Dim1")) \
            .add_properties_to_row_axis(DimensionProperty.of("Dim1", "Code and Name")) \
            .columns_non_empty() \
            .add_hierarchy_set_to_column_axis(MdxHierarchySet.member(Member.of("Dim2", "Elem2"))) \
            .add_properties_to_column_axis(DimensionProperty.of("Dim2", "Name")) \
            .where(Member.of("Dim3", "Elem3"), Member.of("Dim4", "Elem4")) \
            .to_mdx()

        self.assertEqual(
            "SELECT\r\n"
            "NON EMPTY {[dim2].[dim2].[elem2]} DIMENSION PROPERTIES [dim2].[dim2].[name] ON 0,\r\n"
            "NON EMPTY {TM1FILTERBYLEVEL({TM1SUBSETALL([dim1].[dim1])},0)} "
            "DIMENSION PROPERTIES [dim1].[dim1].[codeandname] ON 1\r\n"
            "FROM [cube]\r\n"
            "WHERE ([dim3].[dim3].[elem3],[dim4].[dim4].[elem4])",
            mdx)

    def test_mdx_builder_tm1_ignore_bad_tuples(self):
        mdx = MdxBuilder.from_cube("cube") \
            .tm1_ignore_bad_tuples() \
            .rows_non_empty() \
            .add_hierarchy_set_to_row_axis(MdxHierarchySet.all_leaves("Dim1")) \
            .columns_non_empty() \
            .add_hierarchy_set_to_column_axis(MdxHierarchySet.member(Member.of("Dim2", "Elem2"))) \
            .where(Member.of("Dim3", "Elem3"), Member.of("Dim4", "Elem4")) \
            .to_mdx()

        self.assertEqual(
            "SELECT\r\n"
            "NON EMPTY TM1IGNORE_BADTUPLES {[dim2].[dim2].[elem2]} DIMENSION PROPERTIES MEMBER_NAME ON 0,\r\n"
            "NON EMPTY TM1IGNORE_BADTUPLES {TM1FILTERBYLEVEL({TM1SUBSETALL([dim1].[dim1])},0)} DIMENSION PROPERTIES MEMBER_NAME ON 1\r\n"
            "FROM [cube]\r\n"
            "WHERE ([dim3].[dim3].[elem3],[dim4].[dim4].[elem4])",
            mdx)

    def test_mdx_builder_single_axes(self):
        mdx = MdxBuilder.from_cube("cube") \
            .add_hierarchy_set_to_axis(0, MdxHierarchySet.member(Member.of("Dim1", "Elem1"))) \
            .to_mdx()

        self.assertEqual(
            "SELECT\r\n"
            "{[dim1].[dim1].[elem1]} DIMENSION PROPERTIES MEMBER_NAME ON 0\r\n"
            "FROM [cube]",
            mdx)

    def test_mdx_builder_multi_axes(self):
        mdx = MdxBuilder.from_cube("cube") \
            .add_hierarchy_set_to_axis(0, MdxHierarchySet.member(Member.of("Dim1", "Elem1"))) \
            .add_hierarchy_set_to_axis(1, MdxHierarchySet.member(Member.of("Dim2", "Elem2"))) \
            .add_hierarchy_set_to_axis(2, MdxHierarchySet.member(Member.of("Dim3", "Elem3"))) \
            .add_hierarchy_set_to_axis(3, MdxHierarchySet.member(Member.of("Dim4", "Elem4"))) \
            .add_hierarchy_set_to_axis(4, MdxHierarchySet.member(Member.of("Dim5", "Elem5"))) \
            .to_mdx()

        self.assertEqual(
            "SELECT\r\n"
            "{[dim1].[dim1].[elem1]} DIMENSION PROPERTIES MEMBER_NAME ON 0,\r\n"
            "{[dim2].[dim2].[elem2]} DIMENSION PROPERTIES MEMBER_NAME ON 1,\r\n"
            "{[dim3].[dim3].[elem3]} DIMENSION PROPERTIES MEMBER_NAME ON 2,\r\n"
            "{[dim4].[dim4].[elem4]} DIMENSION PROPERTIES MEMBER_NAME ON 3,\r\n"
            "{[dim5].[dim5].[elem5]} DIMENSION PROPERTIES MEMBER_NAME ON 4\r\n"
            "FROM [cube]",
            mdx)

    def test_mdx_builder_multi_no_where(self):
        mdx = MdxBuilder.from_cube("cube") \
            .rows_non_empty() \
            .add_hierarchy_set_to_row_axis(MdxHierarchySet.all_leaves("Dim1")) \
            .columns_non_empty() \
            .add_hierarchy_set_to_column_axis(MdxHierarchySet.member(Member.of("Dim2", "Elem2"))) \
            .to_mdx()

        self.assertEqual(
            "SELECT\r\n"
            "NON EMPTY {[dim2].[dim2].[elem2]} DIMENSION PROPERTIES MEMBER_NAME ON 0,\r\n"
            "NON EMPTY {TM1FILTERBYLEVEL({TM1SUBSETALL([dim1].[dim1])},0)} DIMENSION PROPERTIES MEMBER_NAME ON 1\r\n"
            "FROM [cube]",
            mdx)

    def test_mdx_builder_multi_fail_combine_sets_tuples_on_axis(self):
        with pytest.raises(ValueError):
            MdxBuilder.from_cube("cube") \
                .rows_non_empty() \
                .add_hierarchy_set_to_axis(0, MdxHierarchySet.all_leaves("Dim1")) \
                .add_member_tuple_to_axis(0, Member.of("Dim1", "Dim1", "Elem1")) \
                .to_mdx()

    def test_mdx_builder_multi_fail_combine_tuples_sets_on_axis(self):
        with pytest.raises(ValueError):
            MdxBuilder.from_cube("cube") \
                .rows_non_empty() \
                .add_member_tuple_to_axis(0, Member.of("Dim1", "Dim1", "Elem1")) \
                .add_hierarchy_set_to_axis(0, MdxHierarchySet.all_leaves("Dim1")) \
                .to_mdx()

    def test_mdx_builder_with_calculated_member(self):
        mdx = MdxBuilder.from_cube(cube="Cube").with_member(
            CalculatedMember.avg(
                dimension="Period",
                hierarchy="Period",
                element="AVG 2016",
                cube="Cube",
                mdx_set=MdxHierarchySet.children(member=Member.of("Period", "2016")),
                mdx_tuple=MdxTuple.of(Member.of("Dim1", "Total Dim1"),
                                      Member.of("Dim2", "Total Dim2")))) \
            .rows_non_empty() \
            .add_hierarchy_set_to_row_axis(MdxHierarchySet.all_leaves("dim1", "dim1")) \
            .columns_non_empty() \
            .add_member_tuple_to_columns(Member.of("Period", "AVG 2016")) \
            .where("[Dim2].[Total Dim2]") \
            .to_mdx()

        self.assertEqual(
            "WITH\r\n"
            "MEMBER [period].[period].[avg2016] AS AVG({[period].[period].[2016].CHILDREN},"
            "[cube].([dim1].[dim1].[totaldim1],[dim2].[dim2].[totaldim2]))\r\n"
            "SELECT\r\n"
            "NON EMPTY {([period].[period].[avg2016])} DIMENSION PROPERTIES MEMBER_NAME ON 0,\r\n"
            "NON EMPTY {TM1FILTERBYLEVEL({TM1SUBSETALL([dim1].[dim1])},0)} DIMENSION PROPERTIES MEMBER_NAME ON 1\r\n"
            "FROM [cube]\r\n"
            "WHERE ([dim2].[dim2].[totaldim2])",
            mdx)

    def test_mdx_builder_with_calculated_member_with_properties(self):
        mdx = MdxBuilder.from_cube(cube="Cube").with_member(
            CalculatedMember.avg(
                dimension="Period",
                hierarchy="Period",
                element="AVG 2016",
                cube="Cube",
                mdx_set=MdxHierarchySet.children(member=Member.of("Period", "2016")),
                mdx_tuple=MdxTuple.of(Member.of("Dim1", "Total Dim1"),
                                      Member.of("Dim2", "Total Dim2")))) \
            .rows_non_empty() \
            .add_hierarchy_set_to_row_axis(MdxHierarchySet.all_leaves("dim1", "dim1")) \
            .columns_non_empty() \
            .add_member_tuple_to_columns(Member.of("Period", "AVG 2016")) \
            .where("[Dim2].[Total Dim2]") \
            .add_properties_to_row_axis("[Dim1].[Code and Name]") \
            .to_mdx()

        self.assertEqual(
            "WITH\r\n"
            "MEMBER [period].[period].[avg2016] AS AVG({[period].[period].[2016].CHILDREN},"
            "[cube].([dim1].[dim1].[totaldim1],[dim2].[dim2].[totaldim2]))\r\n"
            "SELECT\r\n"
            "NON EMPTY {([period].[period].[avg2016])} DIMENSION PROPERTIES MEMBER_NAME ON 0,\r\n"
            "NON EMPTY {TM1FILTERBYLEVEL({TM1SUBSETALL([dim1].[dim1])},0)} DIMENSION PROPERTIES [dim1].[dim1].[codeandname] ON 1\r\n"
            "FROM [cube]\r\n"
            "WHERE ([dim2].[dim2].[totaldim2])",
            mdx)

    def test_mdx_build_with_multi_calculated_member(self):
        mdx = MdxBuilder.from_cube(cube="Cube").with_member(
            CalculatedMember.avg(
                dimension="Period",
                hierarchy="Period",
                element="AVG 2016",
                cube="Cube",
                mdx_set=MdxHierarchySet.children(member=Member.of("Period", "2016")),
                mdx_tuple=MdxTuple.of(Member.of("Dim1", "Total Dim1"),
                                      Member.of("Dim2", "Total Dim2")))) \
            .with_member(
            CalculatedMember.sum(
                dimension="Period",
                hierarchy="Period",
                element="SUM 2016",
                cube="Cube",
                mdx_set=MdxHierarchySet.children(member=Member.of("Period", "2016")),
                mdx_tuple=MdxTuple.of(Member.of("Dim1", "Total Dim1"),
                                      Member.of("Dim2", "Total Dim2")))) \
            .rows_non_empty() \
            .add_hierarchy_set_to_row_axis(MdxHierarchySet.all_leaves("dim1", "dim1")) \
            .columns_non_empty() \
            .add_hierarchy_set_to_column_axis(
            MdxHierarchySet.members(members=[Member.of("Period", "AVG 2016"), Member.of("Period", "SUM 2016")])) \
            .where(Member.of("Dim2", "Total Dim2")) \
            .to_mdx()

        self.assertEqual(
            "WITH\r\n"
            "MEMBER [period].[period].[avg2016] AS AVG({[period].[period].[2016].CHILDREN},"
            "[cube].([dim1].[dim1].[totaldim1],[dim2].[dim2].[totaldim2]))\r\n"
            "MEMBER [period].[period].[sum2016] AS SUM({[period].[period].[2016].CHILDREN},"
            "[cube].([dim1].[dim1].[totaldim1],[dim2].[dim2].[totaldim2]))\r\n"
            "SELECT\r\n"
            "NON EMPTY {[period].[period].[avg2016],[period].[period].[sum2016]} DIMENSION PROPERTIES MEMBER_NAME ON 0,\r\n"
            "NON EMPTY {TM1FILTERBYLEVEL({TM1SUBSETALL([dim1].[dim1])},0)} DIMENSION PROPERTIES MEMBER_NAME ON 1\r\n"
            "FROM [cube]\r\n"
            "WHERE ([dim2].[dim2].[totaldim2])",
            mdx)

    def test_mdx_builder_to_mdx_skip_dimension_properties(self):
        mdx = MdxBuilder.from_cube("cube") \
            .rows_non_empty() \
            .add_hierarchy_set_to_row_axis(MdxHierarchySet.all_leaves("Dim1")) \
            .columns_non_empty() \
            .add_hierarchy_set_to_column_axis(MdxHierarchySet.member(Member.of("Dim2", "Elem2"))) \
            .where(Member.of("Dim3", "Elem3"), Member.of("Dim4", "Elem4")) \
            .to_mdx(skip_dimension_properties=True)

        self.assertEqual(
            "SELECT\r\n"
            "NON EMPTY {[dim2].[dim2].[elem2]} ON 0,\r\n"
            "NON EMPTY {TM1FILTERBYLEVEL({TM1SUBSETALL([dim1].[dim1])},0)} ON 1\r\n"
            "FROM [cube]\r\n"
            "WHERE ([dim3].[dim3].[elem3],[dim4].[dim4].[elem4])",
            mdx)

    def test_mdx_builder_to_mdx_head_tail_columns(self):
        mdx = MdxBuilder.from_cube("cube") \
            .add_hierarchy_set_to_column_axis(MdxHierarchySet.all_leaves("Dim1")) \
            .columns_non_empty() \
            .add_hierarchy_set_to_column_axis(MdxHierarchySet.member(Member.of("Dim2", "Elem2"))) \
            .where(Member.of("Dim3", "Elem3"), Member.of("Dim4", "Elem4")) \
            .to_mdx(head_columns=2, tail_columns=1)

        self.assertEqual(
            "SELECT\r\n"
            "NON EMPTY {TAIL({HEAD({TM1FILTERBYLEVEL({TM1SUBSETALL([dim1].[dim1])},0)} * {[dim2].[dim2].[elem2]}, 2)}, 1)} "
            "DIMENSION PROPERTIES MEMBER_NAME ON 0\r\n"
            "FROM [cube]\r\n"
            "WHERE ([dim3].[dim3].[elem3],[dim4].[dim4].[elem4])",
            mdx)

    def test_mdx_builder_to_mdx_head_tail_rows_and_columns(self):
        mdx = MdxBuilder.from_cube("cube") \
            .add_hierarchy_set_to_column_axis(MdxHierarchySet.all_leaves("Dim1")) \
            .columns_non_empty() \
            .add_hierarchy_set_to_row_axis(MdxHierarchySet.all_leaves("Dim2")) \
            .rows_non_empty() \
            .where(Member.of("Dim3", "Elem3"), Member.of("Dim4", "Elem4")) \
            .to_mdx(head_columns=4, tail_columns=2, head_rows=2, tail_rows=1)

        self.assertEqual(
            "SELECT\r\n"
            "NON EMPTY {TAIL({HEAD({TM1FILTERBYLEVEL({TM1SUBSETALL([dim1].[dim1])},0)}, 4)}, 2)} "
            "DIMENSION PROPERTIES MEMBER_NAME ON 0,\r\n"
            "NON EMPTY {TAIL({HEAD({TM1FILTERBYLEVEL({TM1SUBSETALL([dim2].[dim2])},0)}, 2)}, 1)} "
            "DIMENSION PROPERTIES MEMBER_NAME ON 1\r\n"
            "FROM [cube]\r\n"
            "WHERE ([dim3].[dim3].[elem3],[dim4].[dim4].[elem4])",
            mdx)

    def test_OrderType_ASC(self):
        order = Order("asc")
        self.assertEqual(order, Order.ASC)

        order = Order("ASC")
        self.assertEqual(order, Order.ASC)
        self.assertEqual("ASC", str(order))

    def test_OrderType_DESC(self):
        order = Order("desc")
        self.assertEqual(order, Order.DESC)

        order = Order("DESC")
        self.assertEqual(order, Order.DESC)
        self.assertEqual("DESC", str(order))

    def test_OrderType_BASC(self):
        order = Order("basc")
        self.assertEqual(order, Order.BASC)

        order = Order("BASC")
        self.assertEqual(order, Order.BASC)
        self.assertEqual("BASC", str(order))

    def test_OrderType_BDESC(self):
        order = Order("bdesc")
        self.assertEqual(order, Order.BDESC)

        order = Order("BDESC")
        self.assertEqual(order, Order.BDESC)
        self.assertEqual("BDESC", str(order))

    def test_OrderType_invalid(self):
        with pytest.raises(ValueError):
            Order("no_order")

    def test_ElementType_NUMERIC(self):
        element_type = ElementType("numeric")
        self.assertEqual(element_type, ElementType.NUMERIC)

        element_type = ElementType("NUMERIC")
        self.assertEqual(element_type, ElementType.NUMERIC)
        self.assertEqual("NUMERIC", str(element_type))

    def test_ElementType_STRING(self):
        element_type = ElementType("string")
        self.assertEqual(element_type, ElementType.STRING)

        element_type = ElementType("STRING")
        self.assertEqual(element_type, ElementType.STRING)
        self.assertEqual("STRING", str(element_type))

    def test_ElementType_CONSOLIDATED(self):
        element_type = ElementType("consolidated")
        self.assertEqual(element_type, ElementType.CONSOLIDATED)

        element_type = ElementType("CONSOLIDATED")
        self.assertEqual(element_type, ElementType.CONSOLIDATED)
        self.assertEqual("CONSOLIDATED", str(element_type))

    def test_ElementType_invalid(self):
        with pytest.raises(ValueError):
            ElementType("no_element_type")

    def test_add_empty_set_to_axis_happy_case(self):
        mdx = MdxBuilder.from_cube("Cube") \
            .add_hierarchy_set_to_column_axis(MdxHierarchySet.tm1_subset_all("Dimension")) \
            .add_empty_set_to_axis(1) \
            .to_mdx()
        self.assertEqual(
            mdx,
            "SELECT\r\n"
            "{TM1SUBSETALL([dimension].[dimension])} DIMENSION PROPERTIES MEMBER_NAME ON 0,\r\n"
            "{} DIMENSION PROPERTIES MEMBER_NAME ON 1\r\n"
            "FROM [cube]")

    def test_add_empty_set_to_axis_error(self):
        with pytest.raises(ValueError):
            MdxBuilder.from_cube("Cube") \
                .add_hierarchy_set_to_column_axis(MdxHierarchySet.tm1_subset_all("Dimension1")) \
                .add_hierarchy_set_to_axis(1, MdxHierarchySet.tm1_subset_all("Dimension2")) \
                .add_empty_set_to_axis(1) \
                .to_mdx()

    def test_member_unique_name_short_notation_true(self):
        Member.SHORT_NOTATION = True
        member = Member.of("Dimension1", "Element1")

        self.assertEqual(
            "[dimension1].[element1]",
            member.unique_name)

    def test_member_unique_name_short_notation_false(self):
        Member.SHORT_NOTATION = False
        member = Member.of("Dimension1", "Element1")

        self.assertEqual(
            "[dimension1].[dimension1].[element1]",
            member.unique_name)

    def test_level_expression_number(self):
        level = MdxLevelExpression.level_number(8, "Dimension1", "Hierarchy1")
        self.assertEqual("[dimension1].[hierarchy1].LEVELS(8)", level.to_mdx())

    def test_level_expression_name(self):
        level = MdxLevelExpression.level_name('NamedLevel', "Dimension1", "Hierarchy1")
        self.assertEqual("[dimension1].[hierarchy1].LEVELS('NamedLevel')", level.to_mdx())

    def test_level_expression_member_level(self):
        level = MdxLevelExpression.member_level(Member.of("Dimension1", "Hierarchy1", "Element1"))
        self.assertEqual("[dimension1].[hierarchy1].[element1].LEVEL", level.to_mdx())
