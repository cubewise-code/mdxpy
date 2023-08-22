![Logo](./images/logo.png)


## MDXpy

A simple, yet elegant MDX library for TM1

## Install

    pip install mdxpy

## Usage

Create MDX queries programmatically with the `Member`, `MdxTuple`, `MdxHierarchySet`, `MdxBuilder` classes.

Benefits of using MDXpy over hacking raw MDX queries in your code
- Faster to write
- Requires less MDX knowledge
- Eliminates syntax errors (e.g. forget `}`, `]`, `)` in a query) forever
- Makes code more robust and easier to refactor
- Escaping of `]` in object names is taken care of 

### Member

`Member` is used in `MdxTuple` and `MdxHierarchySet`. 
create a `Member` with the static `Member.of(*args: str)` method.

``` python
>>> member = Member.of("Product", "Product1")
>>> print(member.unique_name)
[PRODUCT].[PRODUCT].[PRODUCT1]

>>> member = Member.of("Region", "ByGeography", "UK")
>>> print(member.unique_name)
[REGION].[BYGEOGRAPHY].[UK]
```

### MdxTuple

Create a `MdxTuple` with the static `of(*args: Member)` method. The MDX expression of the tuple is generated with the `to_mdx` method.

``` python
>>> mdx_tuple = MdxTuple.of(Member.of("Product", "Product1"), Member.of("Region", "US"))

>>> print(mdx_tuple.to_mdx())
([PRODUCT].[PRODUCT].[PRODUCT1],[REGION].[REGION].[US])

>>> mdx_tuple = MdxTuple.of(Member.of("Product", "ByType", "Product1"), Member.of("Region", "ByGeography", "North America"))

>>> print(mdx_tuple.to_mdx())
([PRODUCT].[BYTYPE].[PRODUCT1],[REGION].[BYGEOGRAPHY].[North America])

```     

you can add a `Member` to a `MdxTuple`

``` python
>>> mdx_tuple = MdxTuple.of(Member.of("Product", "ByType", "Product1"))

>>> mdx_tuple.add_member(Member.of("Region", "ByGeography", "North America"))

>>> print(mdx_tuple.to_mdx())
([PRODUCT].[BYTYPE].[PRODUCT1],[REGION].[BYGEOGRAPHY].[NORTHAMERICA])
```

### MdxHierarchySet

`MdxHierarchySet` is created with any of the static methods on the `MdxHierarchySet` class. The `MDX` expression of the set is generated with the `to_mdx` method.

``` python
>>> mdx_set = MdxHierarchySet.tm1_subset_all("Product")
>>> print(mdx_set.to_mdx())
{TM1SUBSETALL([Product].[Product])}

>>> mdx_set = MdxHierarchySet.tm1_subset_to_set("Region", "By Geography", "Default")
>>> print(mdx_set.to_mdx())
{TM1SUBSETTOSET([REGION].[BYGEOGRAPHY],'Default')}

>>> mdx_set = MdxHierarchySet.all_leaves("Region")
>>> print(mdx_set.to_mdx())
{TM1FILTERBYLEVEL({TM1SUBSETALL([REGION].[REGION])},0)}

>>> mdx_set = MdxHierarchySet.members([Member.of("Region", "US"), Member.of("Product", "Product1")])
>>> print(mdx_set.to_mdx())
{[REGION].[REGION].[US],[PRODUCT].[PRODUCT].[PRODUCT1]}
```

Functions on `MdxHierarchySet` can be concatenated to arbitrary length in a functional style:

``` python
>>> mdx_set = MdxHierarchySet.tm1_subset_all("Region").filter_by_level(0).filter_by_pattern("I*").tm1_sort()
>>> print(mdx_set.to_mdx())
{TM1SORT({TM1FILTERBYPATTERN({TM1FILTERBYLEVEL({TM1SUBSETALL([REGION].[REGION])},0)},'I*')},ASC)}
```

### MdxBuilder

The `MdxBuilder` is used to build MDX queries. `MdxHierarchySet` or `MdxTuple` are placed on the axes. Zero suppression can be switched on or off per axis. The actual `MDX` expression is generated with the `to_mdx` method. 

``` python
>>> query = MdxBuilder.from_cube("Cube").add_hierarchy_set_to_column_axis(MdxHierarchySet.all_leaves("Product"))
>>> print(query.to_mdx())
SELECT {TM1FILTERBYLEVEL({TM1SUBSETALL([PRODUCT].[PRODUCT])},0)} ON 0
FROM [CUBE] 

>>> query = MdxBuilder.from_cube("Cube").add_hierarchy_set_to_column_axis(MdxHierarchySet.member(Member.of("Product", "Product1")))
>>> print(query.to_mdx())
SELECT {[PRODUCT].[PRODUCT].[PRODUCT1]} ON 0
FROM [CUBE] 

>>> query =  MdxBuilder.from_cube("Cube").add_member_tuple_to_axis(0, Member.of("Product", "Product1"), Member.of("Region", "EMEA"))
>>> print(query.to_mdx())
SELECT
{([PRODUCT].[PRODUCT].[PRODUCT1],[REGION].[REGION].[EMEA])} ON 0
FROM [CUBE] 

>>> query = MdxBuilder.from_cube("Cube").columns_non_empty().add_hierarchy_set_to_column_axis(MdxHierarchySet.member(Member.of("Product", "Product1")))
>>> print(query.to_mdx())
SELECT
NON EMPTY {[PRODUCT].[PRODUCT].[PRODUCT1]} ON 0 
FROM [CUBE]
```

MDX queries can have any number of axes. Axis 0 _(=columns)_ must be defined.

``` python
>>> mdx = MdxBuilder.from_cube("Cube") \
    .add_hierarchy_set_to_axis(0, MdxHierarchySet.member(Member.of("Region", "US"))) \
    .add_hierarchy_set_to_axis(1, MdxHierarchySet.all_leaves("Product")) \
    .add_hierarchy_set_to_axis(2, MdxHierarchySet.member(Member.of("Version", "Actual"))) \
    .add_hierarchy_set_to_axis(3, MdxHierarchySet.tm1_subset_to_set("Time", "Time", "2020-Q1")) \
    .to_mdx()

>>> print(mdx)
SELECT
{[REGION].[REGION].[US]} ON 0,
{TM1FILTERBYLEVEL({TM1SUBSETALL([PRODUCT].[PRODUCT])},0)} ON 1,
{[VERSION].[VERSION].[ACTUAL]} ON 2,
{TM1SUBSETTOSET([TIME].[TIME],'2020-Q1')} ON 3
FROM [CUBE]
```


### MultiMdxBuilder

The `MultiMdxBuilder` can be used to build a List of MDX queries based on subsets.

``` python
>>> from mdxpy import MdxHierarchySet, MultiMdxBuilder

>>> query = MultiMdxBuilder.from_cube(
    cube="Cube",
    multi_dimension='Month',
    multi_hierarchy='Month',
    multi_subsets=['Q1', 'Q2', 'Q3', 'Q4'],
    multi_axis=1)
    
>>> queries = query.add_hierarchy_set_to_column_axis(MdxHierarchySet.all_leaves("Product"))
>>> print(queries)
['SELECT\r\n{TM1FILTERBYLEVEL({TM1SUBSETALL([product].[product])},0)} DIMENSION PROPERTIES MEMBER_NAME ON 0,\r\n{TM1SUBSETTOSET([month].[month],"Q1")} DIMENSION PROPERTIES MEMBER_NAME ON 1\r\nFROM [cube]', 'SELECT\r\n{TM1FILTERBYLEVEL({TM1SUBSETALL([product].[product])},0)} DIMENSION PROPERTIES MEMBER_NAME ON 0,\r\n{TM1SUBSETTOSET([month].[month],"Q2")} DIMENSION PROPERTIES MEMBER_NAME ON 1\r\nFROM [cube]', 'SELECT\r\n{TM1FILTERBYLEVEL({TM1SUBSETALL([product].[product])},0)} DIMENSION PROPERTIES MEMBER_NAME ON 0,\r\n{TM1SUBSETTOSET([month].[month],"Q3")} DIMENSION PROPERTIES MEMBER_NAME ON 1\r\nFROM [cube]', 'SELECT\r\n{TM1FILTERBYLEVEL({TM1SUBSETALL([product].[product])},0)} DIMENSION PROPERTIES MEMBER_NAME ON 0,\r\n{TM1SUBSETTOSET([month].[month],"Q4")} DIMENSION PROPERTIES MEMBER_NAME ON 1\r\nFROM [cube]']
```

This can be used to great effect in conjunction with TM1py's `execute_mdx_dataframe_async` function.


The `CalculatedMember` class is used to define query-scoped calculated members. They are used with the `MdxBuilder` through the `with_member` function.

``` python
>>> mdx = MdxBuilder.from_cube(cube="Record Rating").with_member(
        CalculatedMember.avg(
            dimension="Period",
            hierarchy="Period",
            element="AVG 2016",
            cube="Record Rating",
            mdx_set=MdxHierarchySet.children(member=Member.of("Period", "2016")),
            mdx_tuple=MdxTuple.of(Member.of("Chart", "Total Charts"), Member.of("Record Rating Measure", "Rating")))) \
        .add_hierarchy_set_to_row_axis(
        MdxHierarchySet
            .children(Member.of("Record", "Total Records"))
            .top_count(cube="Record Rating", mdx_tuple=MdxTuple.of(Member.of("Period", "AVG 2016")), top=5)) \
        .add_member_tuple_to_columns(Member.of("Period", "AVG 2016")) \
        .where(Member.of("Chart", "Total Charts"), Member.of("Record Rating Measure", "Rating")) \
        .to_mdx()

>>> print(mdx)
WITH 
MEMBER [PERIOD].[PERIOD].[AVG2016] AS AVG({[PERIOD].[PERIOD].[2016].CHILDREN},[Record Rating].([CHART].[CHART].[TOTALCHARTS],[RECORDRATINGMEASURE].[RECORDRATINGMEASURE].[RATING]))
SELECT
{([PERIOD].[PERIOD].[AVG2016])} ON 0,
{TOPCOUNT({[RECORD].[RECORD].[TOTALRECORDS].CHILDREN},5,[RECORDRATING].([PERIOD].[PERIOD].[AVG2016]))} ON 1
FROM [RECORDRATING]
WHERE ([CHART].[CHART].[TOTALCHARTS],[RECORDRATINGMEASURE].[RECORDRATINGMEASURE].[RATING])
```

The `DimensionProperty` class is used to query attributes in conjunction with data. 
It is used with the `MdxBuilder` through the `add_properties_to_row_axis`, `add_hierarchy_set_to_column_axis` functions.

``` python
from mdxpy import DimensionProperty, MdxHierarchySet, MdxBuilder, Member

query = MdxBuilder.from_cube("Sales")

query = query.rows_non_empty()
query = query.add_hierarchy_set_to_row_axis(MdxHierarchySet.all_leaves("Product"))
query = query.add_properties_to_row_axis(DimensionProperty.of("Product", "Description"))

query = query.columns_non_empty()
query = query.add_hierarchy_set_to_column_axis(MdxHierarchySet.member(Member.of("Sales Measure", "Revenue")))

query = query.where(Member.of("Year", "2022"), Member.of("Region", "Switzerland"))

print(query.to_mdx())

>>> print(mdx)
SELECT
NON EMPTY {[salesmeasure].[salesmeasure].[revenue]} DIMENSION PROPERTIES MEMBER_NAME ON 0,
NON EMPTY {TM1FILTERBYLEVEL({TM1SUBSETALL([product].[product])},0)} DIMENSION PROPERTIES [product].[product].[description] ON 1
FROM [sales]
WHERE ([year].[year].[2022],[region].[region].[switzerland])
```

To see all samples checkout the `test.py` file

## Supported MDX Functions

- TM1SUBSETALL
- MEMBERS
- TM1SUBSETTOSET
- DEFAULTMEMBER
- PARENT
- FIRSTCHILD
- LASTCHILD
- CHILDREN
- ANCESTORS
- ANCESTOR
- DRILLDOWNLEVEL
- FILTER
- TM1FILTERBYPATTERN
- TM1FILTERBYLEVEL
- TM1SORT
- HEAD
- TAIL
- SUBSET
- TOPCOUNT
- BOTTOMCOUNT
- UNION
- INTERSECT
- EXCEPT
- ORDER

## Tests

All tests in `test.py`

## Contribution

Contribution is welcome. If you find a bug or feel like you can contribute please fork the repository, update the code and then create a pull request so we can merge in the changes.