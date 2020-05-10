import unittest

import pytest
from ordered_set import OrderedSet

from mdxpy import Member, MdxTuple, MdxHierarchySet, normalize, MdxBuilder, CalculatedMember
from mdxpy.mdx import Order


class Test(unittest.TestCase):

    def test_normalize_simple(self):
        value = normalize("ele ment")
        self.assertEqual(value, "ELEMENT")

    def test_normalize_escape_bracket(self):
        value = normalize("ele me]nt")
        self.assertEqual(value, "ELEME]]NT")

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
        self.assertEqual(element.unique_name, "[DIM].[DIM].[ELEM]")

    def test_member_unique_name_with_hierarchy(self):
        element = Member.of("Dim", "Hier", "Elem")
        self.assertEqual(element.unique_name, "[DIM].[HIER].[ELEM]")

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
            "MEMBER [PERIOD].[PERIOD].[AVG2016] AS AVG({[PERIOD].[PERIOD].[2016].CHILDREN},[CUBE]."
            "([DIMENSION1].[DIMENSION1].[ELEMENT1],[DIMENSION2].[DIMENSION2].[ELEMENT2]))")

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
            "MEMBER [PERIOD].[PERIOD].[SUM2016] AS SUM({[PERIOD].[PERIOD].[2016].CHILDREN},[CUBE]."
            "([DIMENSION1].[DIMENSION1].[ELEMENT1],[DIMENSION2].[DIMENSION2].[ELEMENT2]))")

    def test_calculated_member_lookup_attribute(self):
        calculated_member = CalculatedMember.lookup_attribute(
            dimension="Period",
            hierarchy="Period",
            element="VersionAttribute1",
            attribute_dimension="Version",
            attribute="Attribute1")

        self.assertEqual(
            calculated_member.to_mdx(),
            "MEMBER [PERIOD].[PERIOD].[VERSIONATTRIBUTE1] AS [}ELEMENTATTRIBUTES_VERSION]."
            "([}ELEMENTATTRIBUTES_VERSION].[ATTRIBUTE1])")

    def test_calculated_member_lookup(self):
        calculated_member = CalculatedMember.lookup(
            "Period",
            "Period",
            "VersionAttribute1",
            cube="}ElementAttributes_Version",
            mdx_tuple=MdxTuple.of(Member.of("}ElementAttributes_Version", "Attribute1")))

        self.assertEqual(
            calculated_member.to_mdx(),
            "MEMBER [PERIOD].[PERIOD].[VERSIONATTRIBUTE1] AS [}ELEMENTATTRIBUTES_VERSION]."
            "([}ELEMENTATTRIBUTES_VERSION].[}ELEMENTATTRIBUTES_VERSION].[ATTRIBUTE1])")

    def test_mdx_tuple_empty(self):
        tupl = MdxTuple.empty()
        self.assertEqual(tupl.members, OrderedSet())

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

    def test_mdx_tuple_add_duplicate_element(self):
        tupl = MdxTuple.of(Member.of("Dimension1", "Hierarchy1", "Element1"))
        tupl.add_member(Member.of("Dimension1", "Hierarchy1", "Element1"))

        self.assertEqual(len(tupl), 1)
        self.assertEqual(tupl.members[0], Member.of("Dimension1", "Hierarchy1", "Element1"))

    def test_mdx_hierarchy_set_tm1_subset_all(self):
        hierarchy_set = MdxHierarchySet.tm1_subset_all("Dimension")
        self.assertEqual(
            "{TM1SUBSETALL([DIMENSION].[DIMENSION])}",
            hierarchy_set.to_mdx())

    def test_mdx_hierarchy_set_all_members(self):
        hierarchy_set = MdxHierarchySet.all_members("Dimension", "Hierarchy")
        self.assertEqual(
            "{[DIMENSION].[HIERARCHY].MEMBERS}",
            hierarchy_set.to_mdx())

    def test_mdx_hierarchy_set_tm1_subset_to_set(self):
        hierarchy_set = MdxHierarchySet.tm1_subset_to_set("Dimension", "Hierarchy", "Default")
        self.assertEqual(
            '{TM1SUBSETTOSET([DIMENSION].[HIERARCHY],"Default")}',
            hierarchy_set.to_mdx())

    def test_mdx_hierarchy_set_all_consolidations(self):
        hierarchy_set = MdxHierarchySet.all_consolidations("Dimension")
        self.assertEqual(
            "{EXCEPT("
            "{TM1SUBSETALL([DIMENSION].[DIMENSION])},"
            "{TM1FILTERBYLEVEL({TM1SUBSETALL([DIMENSION].[DIMENSION])},0)})}",
            hierarchy_set.to_mdx())

    def test_mdx_hierarchy_set_all_leaves(self):
        hierarchy_set = MdxHierarchySet.all_leaves("Dimension")
        self.assertEqual("{TM1FILTERBYLEVEL({TM1SUBSETALL([DIMENSION].[DIMENSION])},0)}", hierarchy_set.to_mdx())

    def test_mdx_hierarchy_set_default_member(self):
        hierarchy_set = MdxHierarchySet.default_member("Dimension")
        self.assertEqual("{[DIMENSION].[DIMENSION].DEFAULTMEMBER}", hierarchy_set.to_mdx())

    def test_mdx_hierarchy_set_elements(self):
        hierarchy_set = MdxHierarchySet.members(
            [Member.of("Dimension", "element1"), Member.of("Dimension", "element2")])
        self.assertEqual(
            "{[DIMENSION].[DIMENSION].[ELEMENT1],[DIMENSION].[DIMENSION].[ELEMENT2]}",
            hierarchy_set.to_mdx())

    def test_mdx_hierarchy_set_parent(self):
        hierarchy_set = MdxHierarchySet.parent(Member.of("Dimension", "Element"))

        self.assertEqual(
            "{[DIMENSION].[DIMENSION].[ELEMENT].PARENT}",
            hierarchy_set.to_mdx())

    def test_mdx_hierarchy_set_first_child(self):
        hierarchy_set = MdxHierarchySet.first_child(Member.of("Dimension", "Element"))

        self.assertEqual(
            "{[DIMENSION].[DIMENSION].[ELEMENT].FIRSTCHILD}",
            hierarchy_set.to_mdx())

    def test_mdx_hierarchy_set_last_child(self):
        hierarchy_set = MdxHierarchySet.last_child(Member.of("Dimension", "Element"))

        self.assertEqual(
            "{[DIMENSION].[DIMENSION].[ELEMENT].LASTCHILD}",
            hierarchy_set.to_mdx())

    def test_mdx_hierarchy_set_children(self):
        hierarchy_set = MdxHierarchySet.children(Member.of("Dimension", "Element"))

        self.assertEqual(
            "{[DIMENSION].[DIMENSION].[ELEMENT].CHILDREN}",
            hierarchy_set.to_mdx())

    def test_mdx_hierarchy_set_ancestors(self):
        hierarchy_set = MdxHierarchySet.ancestors(Member.of("Dimension", "Element"))

        self.assertEqual(
            "{[DIMENSION].[DIMENSION].[ELEMENT].ANCESTORS}",
            hierarchy_set.to_mdx())

    def test_mdx_hierarchy_set_ancestor(self):
        hierarchy_set = MdxHierarchySet.ancestor(Member.of("Dimension", "Element"), 1)

        self.assertEqual(
            "{ANCESTOR([DIMENSION].[DIMENSION].[ELEMENT],1)}",
            hierarchy_set.to_mdx())

    def test_mdx_hierarchy_set_drill_down_level(self):
        hierarchy_set = MdxHierarchySet.drill_down_level(Member.of("Dimension", "Element"))

        self.assertEqual(
            "{DRILLDOWNLEVEL({[DIMENSION].[DIMENSION].[ELEMENT]})}",
            hierarchy_set.to_mdx())

    def test_mdx_hierarchy_set_tm1_drill_down_member_all_recursive(self):
        hierarchy_set = MdxHierarchySet.members([Member.of("DIMENSION", "ELEMENT")]).tm1_drill_down_member(all=True,
                                                                                                           recursive=True)

        self.assertEqual(
            "{TM1DRILLDOWNMEMBER({[DIMENSION].[DIMENSION].[ELEMENT]}, ALL, RECURSIVE)}",
            hierarchy_set.to_mdx())

    def test_mdx_hierarchy_set_tm1_drill_down_member_set_recursive(self):
        hierarchy_set = MdxHierarchySet.members([Member.of("DIMENSION", "ELEMENT")]).tm1_drill_down_member(
            other_set=MdxHierarchySet.members([Member.of("DIMENSION", "ELEMENT")]),
            recursive=True)
        self.assertEqual(
            "{TM1DRILLDOWNMEMBER({[DIMENSION].[DIMENSION].[ELEMENT]}, {[DIMENSION].[DIMENSION].[ELEMENT]}, RECURSIVE)}",
            hierarchy_set.to_mdx())

    def test_mdx_hierarchy_set_tm1_drill_down_member_all(self):
        hierarchy_set = MdxHierarchySet.members([Member.of("DIMENSION", "ELEMENT")]).tm1_drill_down_member(all=True,
                                                                                                           recursive=False)

        self.assertEqual(
            "{TM1DRILLDOWNMEMBER({[DIMENSION].[DIMENSION].[ELEMENT]}, ALL)}",
            hierarchy_set.to_mdx())

    def test_mdx_hierarchy_set_tm1_drill_down_member_set(self):
        hierarchy_set = MdxHierarchySet.members([Member.of("DIMENSION", "ELEMENT")]).tm1_drill_down_member(
            other_set=MdxHierarchySet.members([Member.of("DIMENSION", "ELEMENT")]), recursive=False)
        self.assertEqual(
            "{TM1DRILLDOWNMEMBER({[DIMENSION].[DIMENSION].[ELEMENT]}, {[DIMENSION].[DIMENSION].[ELEMENT]})}",
            hierarchy_set.to_mdx())

    def test_mdx_hierarchy_set_from_str(self):
        hierarchy_set = MdxHierarchySet.from_str(
            dimension="Dimension",
            hierarchy="Hierarchy",
            mdx="{[DIMENSION].[HIERARCHY].MEMBERS}")

        self.assertEqual(hierarchy_set.to_mdx(), "{[DIMENSION].[HIERARCHY].MEMBERS}")

    def test_mdx_hierarchy_set_from_str_with_other(self):
        hierarchy_set = MdxHierarchySet.from_str(
            dimension="Dimension",
            hierarchy="Hierarchy",
            mdx="{[DIMENSION].[HIERARCHY].MEMBERS}").filter_by_attribute("Attribute1", ["Value1"])

        self.assertEqual(
            hierarchy_set.to_mdx(),
            '{FILTER({[DIMENSION].[HIERARCHY].MEMBERS},[}ELEMENTATTRIBUTES_DIMENSION].([}ELEMENTATTRIBUTES_DIMENSION].[Attribute1])="Value1")}')

    def test_mdx_filter_by_attribute_single_string(self):
        hierarchy_set = MdxHierarchySet.tm1_subset_all("Dimension").filter_by_attribute("Attribute1", ["Value1"])
        self.assertEqual(
            "{FILTER({TM1SUBSETALL([DIMENSION].[DIMENSION])},"
            '[}ELEMENTATTRIBUTES_DIMENSION].([}ELEMENTATTRIBUTES_DIMENSION].[Attribute1])="Value1")}',
            hierarchy_set.to_mdx())

    def test_mdx_filter_by_attribute_single_numeric(self):
        hierarchy_set = MdxHierarchySet.tm1_subset_all("Dimension").filter_by_attribute("Attribute1", [1])

        self.assertEqual(
            "{FILTER({TM1SUBSETALL([DIMENSION].[DIMENSION])},"
            "[}ELEMENTATTRIBUTES_DIMENSION].([}ELEMENTATTRIBUTES_DIMENSION].[Attribute1])=1)}",
            hierarchy_set.to_mdx())

    def test_mdx_filter_by_attribute_multiple(self):
        hierarchy_set = MdxHierarchySet.tm1_subset_all("Dimension").filter_by_attribute("Attribute1",
                                                                                        ["Value1", 1, 2.0])

        self.assertEqual(
            '{FILTER({TM1SUBSETALL([DIMENSION].[DIMENSION])},'
            '[}ELEMENTATTRIBUTES_DIMENSION].([}ELEMENTATTRIBUTES_DIMENSION].[Attribute1])="Value1" OR '
            '[}ELEMENTATTRIBUTES_DIMENSION].([}ELEMENTATTRIBUTES_DIMENSION].[Attribute1])=1 OR '
            '[}ELEMENTATTRIBUTES_DIMENSION].([}ELEMENTATTRIBUTES_DIMENSION].[Attribute1])=2.0)}',
            hierarchy_set.to_mdx())

    def test_mdx_hierarchy_set_filter_by_wildcard(self):
        hierarchy_set = MdxHierarchySet.all_members("Dimension", "Hierarchy").filter_by_pattern("2011*")

        self.assertEqual(
            "{TM1FILTERBYPATTERN({[DIMENSION].[HIERARCHY].MEMBERS},'2011*')}",
            hierarchy_set.to_mdx())

    def test_mdx_hierarchy_set_filter_by_level(self):
        hierarchy_set = MdxHierarchySet.all_members("Dimension", "Hierarchy").filter_by_level(0)

        self.assertEqual(
            "{TM1FILTERBYLEVEL({[DIMENSION].[HIERARCHY].MEMBERS},0)}",
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
            "{FILTER({[DIMENSION1].[HIERARCHY1].MEMBERS},"
            "[CUBE].([DIMENSION2].[HIERARCHY2].[ELEMENTA],[DIMENSION3].[HIERARCHY3].[ELEMENTB])=1)}",
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
            "{FILTER({[DIMENSION1].[HIERARCHY1].MEMBERS},"
            "[CUBE].([DIMENSION2].[DIMENSION2].[ELEMENTA],[DIMENSION3].[DIMENSION3].[ELEMENTB])='ABC')}",
            hierarchy_set.to_mdx())

    def test_mdx_hierarchy_set_tm1_sort_asc(self):
        hierarchy_set = MdxHierarchySet.tm1_subset_all("Dimension", "Hierarchy").tm1_sort(True)

        self.assertEqual(
            "{TM1SORT({TM1SUBSETALL([DIMENSION].[HIERARCHY])},ASC)}",
            hierarchy_set.to_mdx())

    def test_mdx_hierarchy_set_tm1_sort_desc(self):
        hierarchy_set = MdxHierarchySet.tm1_subset_all("Dimension").tm1_sort(False)

        self.assertEqual(
            "{TM1SORT({TM1SUBSETALL([DIMENSION].[DIMENSION])},DESC)}",
            hierarchy_set.to_mdx())

    def test_mdx_hierarchy_set_head(self):
        hierarchy_set = MdxHierarchySet.tm1_subset_all("Dimension").head(10)

        self.assertEqual(
            "{HEAD({TM1SUBSETALL([DIMENSION].[DIMENSION])},10)}",
            hierarchy_set.to_mdx())

    def test_mdx_hierarchy_set_tail(self):
        hierarchy_set = MdxHierarchySet.tm1_subset_all("Dimension").tail(10)

        self.assertEqual(
            "{TAIL({TM1SUBSETALL([DIMENSION].[DIMENSION])},10)}",
            hierarchy_set.to_mdx())

    def test_mdx_hierarchy_set_subset(self):
        hierarchy_set = MdxHierarchySet.tm1_subset_all("Dimension").subset(1, 3)

        self.assertEqual(
            "{SUBSET({TM1SUBSETALL([DIMENSION].[DIMENSION])},1,3)}",
            hierarchy_set.to_mdx())

    def test_mdx_hierarchy_set_top_count(self):
        hierarchy_set = MdxHierarchySet \
            .tm1_subset_all("Dimension") \
            .top_count("CUBE", MdxTuple.of(Member.of("DIMENSION2", "ELEMENT2"), Member.of("DIMENSION3", "ELEMENT3")),
                       10)

        self.assertEqual(
            "{TOPCOUNT({TM1SUBSETALL([DIMENSION].[DIMENSION])},"
            "10,"
            "[CUBE].([DIMENSION2].[DIMENSION2].[ELEMENT2],[DIMENSION3].[DIMENSION3].[ELEMENT3]))}",
            hierarchy_set.to_mdx())

    def test_mdx_hierarchy_set_bottom_count(self):
        hierarchy_set = MdxHierarchySet \
            .tm1_subset_all("Dimension") \
            .bottom_count("CUBE", MdxTuple.of(Member.of("DIMENSION2", "ELEMENT2"), Member.of("DIMENSION3", "ELEMENT3")),
                          10)

        self.assertEqual(
            "{BOTTOMCOUNT({TM1SUBSETALL([DIMENSION].[DIMENSION])},"
            "10,"
            "[CUBE].([DIMENSION2].[DIMENSION2].[ELEMENT2],[DIMENSION3].[DIMENSION3].[ELEMENT3]))}",
            hierarchy_set.to_mdx())

    def test_mdx_hierarchy_set_union(self):
        hierarchy_set = MdxHierarchySet.member(Member.of("DIMENSION", "ELEMENT1")). \
            union(MdxHierarchySet.member(Member.of("DIMENSION", "ELEMENT2")))

        self.assertEqual(
            "{UNION({[DIMENSION].[DIMENSION].[ELEMENT1]},{[DIMENSION].[DIMENSION].[ELEMENT2]})}",
            hierarchy_set.to_mdx())

    def test_mdx_hierarchy_set_intersect(self):
        hierarchy_set = MdxHierarchySet.member(Member.of("DIMENSION", "ELEMENT1")). \
            intersect(MdxHierarchySet.member(Member.of("DIMENSION", "ELEMENT2")))

        self.assertEqual(
            "{INTERSECT({[DIMENSION].[DIMENSION].[ELEMENT1]},{[DIMENSION].[DIMENSION].[ELEMENT2]})}",
            hierarchy_set.to_mdx())

    def test_mdx_hierarchy_set_except(self):
        hierarchy_set = MdxHierarchySet.member(Member.of("DIMENSION", "ELEMENT1")). \
            except_(MdxHierarchySet.member(Member.of("DIMENSION", "ELEMENT2")))

        self.assertEqual(
            "{EXCEPT({[DIMENSION].[DIMENSION].[ELEMENT1]},{[DIMENSION].[DIMENSION].[ELEMENT2]})}",
            hierarchy_set.to_mdx())

    def test_mdx_hierarchy_set_order(self):
        hierarchy_set = MdxHierarchySet.all_members("Dimension1", "Hierarchy1").order(
            cube="Cube",
            mdx_tuple=MdxTuple.of(
                Member.of("Dimension2", "Hierarchy2", "ElementA"),
                Member.of("Dimension3", "Hierarchy3", "ElementB")))

        self.assertEqual(
            "{ORDER({[DIMENSION1].[HIERARCHY1].MEMBERS},"
            "[CUBE].([DIMENSION2].[HIERARCHY2].[ELEMENTA],[DIMENSION3].[HIERARCHY3].[ELEMENTB]),BASC)}",
            hierarchy_set.to_mdx())

    def test_mdx_hierarchy_set_order_desc(self):
        hierarchy_set = MdxHierarchySet.all_members("Dimension1", "Hierarchy1").order(
            cube="Cube",
            mdx_tuple=MdxTuple.of(
                Member.of("Dimension2", "Hierarchy2", "ElementA"),
                Member.of("Dimension3", "Hierarchy3", "ElementB")),
            order=Order.DESC)

        self.assertEqual(
            "{ORDER({[DIMENSION1].[HIERARCHY1].MEMBERS},"
            "[CUBE].([DIMENSION2].[HIERARCHY2].[ELEMENTA],[DIMENSION3].[HIERARCHY3].[ELEMENTB]),DESC)}",
            hierarchy_set.to_mdx())

    def test_mdx_hierarchy_set_order_desc_str(self):
        hierarchy_set = MdxHierarchySet.all_members("Dimension1", "Hierarchy1").order(
            cube="Cube",
            mdx_tuple=MdxTuple.of(
                Member.of("Dimension2", "Hierarchy2", "ElementA"),
                Member.of("Dimension3", "Hierarchy3", "ElementB")),
            order="DESC")

        self.assertEqual(
            "{ORDER({[DIMENSION1].[HIERARCHY1].MEMBERS},"
            "[CUBE].([DIMENSION2].[HIERARCHY2].[ELEMENTA],[DIMENSION3].[HIERARCHY3].[ELEMENTB]),DESC)}",
            hierarchy_set.to_mdx())

    def test_mdx_hierarchy_set_order_by_attribute(self):
        hierarchy_set = MdxHierarchySet.all_members("Dimension1", "Hierarchy1").order_by_attribute(
            attribute_name="Attribute1",
            order='asc')

        self.assertEqual(
            '{ORDER({[DIMENSION1].[HIERARCHY1].MEMBERS},'
            '[DIMENSION1].[HIERARCHY1].CURRENTMEMBER.PROPERTIES("ATTRIBUTE1"), ASC)}',
            hierarchy_set.to_mdx())

    def test_mdx_hierarchy_set_generate_attribute_to_member(self):
        hierarchy_set = MdxHierarchySet.all_leaves("Store").generate_attribute_to_member(
            attribute="Manager",
            dimension="Manager")

        self.assertEqual(hierarchy_set.dimension, "MANAGER")

        self.assertEqual(
            "{GENERATE("
            "{TM1FILTERBYLEVEL({TM1SUBSETALL([STORE].[STORE])},0)},"
            "{STRTOMEMBER('[MANAGER].[MANAGER].[' + [STORE].[STORE].CURRENTMEMBER.PROPERTIES(\"Manager\") + ']')})}",
            hierarchy_set.to_mdx())

    def test_mdx_builder_simple(self):
        mdx = MdxBuilder.from_cube("CUBE") \
            .rows_non_empty() \
            .add_hierarchy_set_to_row_axis(MdxHierarchySet.all_leaves("Dim1")) \
            .columns_non_empty() \
            .add_hierarchy_set_to_column_axis(MdxHierarchySet.member(Member.of("Dim2", "Elem2"))) \
            .where(Member.of("Dim3", "Elem3"), Member.of("Dim4", "Elem4")) \
            .to_mdx()

        self.assertEqual(
            "SELECT\r\n"
            "NON EMPTY {[DIM2].[DIM2].[ELEM2]} ON 0,\r\n"
            "NON EMPTY {TM1FILTERBYLEVEL({TM1SUBSETALL([DIM1].[DIM1])},0)} ON 1\r\n"
            "FROM [CUBE]\r\n"
            "WHERE ([DIM3].[DIM3].[ELEM3],[DIM4].[DIM4].[ELEM4])",
            mdx)

    def test_mdx_builder_tm1_ignore_bad_tuples(self):
        mdx = MdxBuilder.from_cube("CUBE") \
            .tm1_ignore_bad_tuples() \
            .rows_non_empty() \
            .add_hierarchy_set_to_row_axis(MdxHierarchySet.all_leaves("Dim1")) \
            .columns_non_empty() \
            .add_hierarchy_set_to_column_axis(MdxHierarchySet.member(Member.of("Dim2", "Elem2"))) \
            .where(Member.of("Dim3", "Elem3"), Member.of("Dim4", "Elem4")) \
            .to_mdx()

        self.assertEqual(
            "SELECT\r\n"
            "NON EMPTY TM1IGNORE_BADTUPLES {[DIM2].[DIM2].[ELEM2]} ON 0,\r\n"
            "NON EMPTY TM1IGNORE_BADTUPLES {TM1FILTERBYLEVEL({TM1SUBSETALL([DIM1].[DIM1])},0)} ON 1\r\n"
            "FROM [CUBE]\r\n"
            "WHERE ([DIM3].[DIM3].[ELEM3],[DIM4].[DIM4].[ELEM4])",
            mdx)

    def test_mdx_builder_single_axes(self):
        mdx = MdxBuilder.from_cube("CUBE") \
            .add_hierarchy_set_to_axis(0, MdxHierarchySet.member(Member.of("Dim1", "Elem1"))) \
            .to_mdx()

        self.assertEqual(
            "SELECT\r\n"
            "{[DIM1].[DIM1].[ELEM1]} ON 0\r\n"
            "FROM [CUBE]",
            mdx)

    def test_mdx_builder_multi_axes(self):
        mdx = MdxBuilder.from_cube("CUBE") \
            .add_hierarchy_set_to_axis(0, MdxHierarchySet.member(Member.of("Dim1", "Elem1"))) \
            .add_hierarchy_set_to_axis(1, MdxHierarchySet.member(Member.of("Dim2", "Elem2"))) \
            .add_hierarchy_set_to_axis(2, MdxHierarchySet.member(Member.of("Dim3", "Elem3"))) \
            .add_hierarchy_set_to_axis(3, MdxHierarchySet.member(Member.of("Dim4", "Elem4"))) \
            .add_hierarchy_set_to_axis(4, MdxHierarchySet.member(Member.of("Dim5", "Elem5"))) \
            .to_mdx()

        self.assertEqual(
            "SELECT\r\n"
            "{[DIM1].[DIM1].[ELEM1]} ON 0,\r\n"
            "{[DIM2].[DIM2].[ELEM2]} ON 1,\r\n"
            "{[DIM3].[DIM3].[ELEM3]} ON 2,\r\n"
            "{[DIM4].[DIM4].[ELEM4]} ON 3,\r\n"
            "{[DIM5].[DIM5].[ELEM5]} ON 4\r\n"
            "FROM [CUBE]",
            mdx)

    def test_mdx_builder_multi_no_where(self):
        mdx = MdxBuilder.from_cube("CUBE") \
            .rows_non_empty() \
            .add_hierarchy_set_to_row_axis(MdxHierarchySet.all_leaves("Dim1")) \
            .columns_non_empty() \
            .add_hierarchy_set_to_column_axis(MdxHierarchySet.member(Member.of("Dim2", "Elem2"))) \
            .to_mdx()

        self.assertEqual(
            "SELECT\r\n"
            "NON EMPTY {[DIM2].[DIM2].[ELEM2]} ON 0,\r\n"
            "NON EMPTY {TM1FILTERBYLEVEL({TM1SUBSETALL([DIM1].[DIM1])},0)} ON 1\r\n"
            "FROM [CUBE]",
            mdx)

    def test_mdx_builder_multi_fail_combine_sets_tuples_on_axis(self):
        with pytest.raises(ValueError):
            MdxBuilder.from_cube("CUBE") \
                .rows_non_empty() \
                .add_hierarchy_set_to_axis(0, MdxHierarchySet.all_leaves("Dim1")) \
                .add_member_tuple_to_axis(0, Member.of("Dim1", "Dim1", "Elem1")) \
                .to_mdx()

    def test_mdx_builder_multi_fail_combine_tuples_sets_on_axis(self):
        with pytest.raises(ValueError):
            MdxBuilder.from_cube("CUBE") \
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
            .add_hierarchy_set_to_row_axis(MdxHierarchySet.all_leaves("DIM1", "DIM1")) \
            .columns_non_empty() \
            .add_member_tuple_to_columns(Member.of("Period", "AVG 2016")) \
            .where("[Dim2].[Total Dim2]") \
            .to_mdx()

        self.assertEqual(
            "WITH\r\n"
            "MEMBER [PERIOD].[PERIOD].[AVG2016] AS AVG({[PERIOD].[PERIOD].[2016].CHILDREN},"
            "[CUBE].([DIM1].[DIM1].[TOTALDIM1],[DIM2].[DIM2].[TOTALDIM2]))\r\n"
            "SELECT\r\n"
            "NON EMPTY {([PERIOD].[PERIOD].[AVG2016])} ON 0,\r\n"
            "NON EMPTY {TM1FILTERBYLEVEL({TM1SUBSETALL([DIM1].[DIM1])},0)} ON 1\r\n"
            "FROM [CUBE]\r\n"
            "WHERE ([DIM2].[DIM2].[TOTALDIM2])",
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
            .add_hierarchy_set_to_row_axis(MdxHierarchySet.all_leaves("DIM1", "DIM1")) \
            .columns_non_empty() \
            .add_hierarchy_set_to_column_axis(
            MdxHierarchySet.members(members=[Member.of("Period", "AVG 2016"), Member.of("Period", "SUM 2016")])) \
            .where(Member.of("Dim2", "Total Dim2")) \
            .to_mdx()

        self.assertEqual(
            "WITH\r\n"
            "MEMBER [PERIOD].[PERIOD].[AVG2016] AS AVG({[PERIOD].[PERIOD].[2016].CHILDREN},"
            "[CUBE].([DIM1].[DIM1].[TOTALDIM1],[DIM2].[DIM2].[TOTALDIM2]))\r\n"
            "MEMBER [PERIOD].[PERIOD].[SUM2016] AS SUM({[PERIOD].[PERIOD].[2016].CHILDREN},"
            "[CUBE].([DIM1].[DIM1].[TOTALDIM1],[DIM2].[DIM2].[TOTALDIM2]))\r\n"
            "SELECT\r\n"
            "NON EMPTY {[PERIOD].[PERIOD].[AVG2016],[PERIOD].[PERIOD].[SUM2016]} ON 0,\r\n"
            "NON EMPTY {TM1FILTERBYLEVEL({TM1SUBSETALL([DIM1].[DIM1])},0)} ON 1\r\n"
            "FROM [CUBE]\r\n"
            "WHERE ([DIM2].[DIM2].[TOTALDIM2])",
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

    def test_add_empty_set_to_axis_happy_case(self):
        mdx = MdxBuilder.from_cube("Cube") \
            .add_hierarchy_set_to_column_axis(MdxHierarchySet.tm1_subset_all("Dimension")) \
            .add_empty_set_to_axis(1) \
            .to_mdx()
        self.assertEqual(
            mdx,
            "SELECT\r\n"
            "{TM1SUBSETALL([DIMENSION].[DIMENSION])} ON 0,\r\n"
            "{} ON 1\r\n"
            "FROM [CUBE]")

    def test_add_empty_set_to_axis_error(self):
        with pytest.raises(ValueError):
            mdx = MdxBuilder.from_cube("Cube") \
                .add_hierarchy_set_to_column_axis(MdxHierarchySet.tm1_subset_all("Dimension1")) \
                .add_hierarchy_set_to_axis(1, MdxHierarchySet.tm1_subset_all("Dimension2")) \
                .add_empty_set_to_axis(1) \
                .to_mdx()
