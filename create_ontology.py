import pandas as pd
from owlready2 import (
    ObjectProperty,
    Thing,
    get_ontology,
    AllDisjoint,
    FunctionalProperty,
    InverseFunctionalProperty,
    TransitiveProperty,
    SymmetricProperty,
    AsymmetricProperty,
    ReflexiveProperty,
    IrreflexiveProperty,
)

MAX_LOOP_COUNT = 100


def create_subclass(parent_class, name, attributes=None):
    if attributes is None:
        attributes = {}
    return type(name, (parent_class,), attributes)


def create_classes_and_subclasses(df):
    class_dict = {}
    unknown_relations = []
    # first, find all children that have no parent...
    for _, row in df.iterrows():
        parent = row["Parent"]
        child = row["ContextInformation"]
        if not isinstance(parent, str):
            # ...these are subclasses of the master class Thing
            class_dict[child] = create_subclass(parent_class=Thing, name=child)
    for _, row in df.iterrows():
        # then, find all children that have parents...
        child = row["ContextInformation"]
        parent = row["Parent"]
        if isinstance(parent, str):
            # ...if they have parents...
            try:
                # ...try to make them a subclass of the parent class.
                child_class = create_subclass(
                    parent_class=class_dict[parent], name=child
                )
                class_dict[child] = child_class
            except KeyError:
                # if the parent class is not yet defined, remember the parent/child relation for later
                unknown_relations.append((parent, child))
    # at this point all children without parents and children with known parents are created.
    # we will now loop through all unknown_relations until all relations could be translated into class relations
    loop_counter = 0
    while unknown_relations and loop_counter < MAX_LOOP_COUNT:
        loop_counter += 1
        for unknown_relation in unknown_relations:
            parent, child = unknown_relation
            if isinstance(parent, str):
                try:
                    child_class = create_subclass(
                        parent_class=class_dict[parent], name=child
                    )
                    class_dict[child] = child_class
                    unknown_relations.remove((parent, child))
                except KeyError:
                    pass
        if loop_counter == MAX_LOOP_COUNT:
            # if the loop could not empty unknown_relations at this point,
            # there is likely a bug or wrong excel entries
            print(
                f"The loop reached its maximum count of {MAX_LOOP_COUNT}. I had to abort here!"
            )
    return class_dict


def create_relationships_between_classes(df, class_dict, dr):

    # mapping of parent class and column name
    name2class = {
        "Functional": FunctionalProperty,
        "InverseFunctional": InverseFunctionalProperty,
        "Transitive": TransitiveProperty,
        "Symmetric": SymmetricProperty,
        "Asymmetric": AsymmetricProperty,
        "Reflexive": ReflexiveProperty,
        "Irreflexive": IrreflexiveProperty,
    }

    fm_property = df.loc[
        (
            (df["RelationshipType"] != "OR")
            & (df["RelationshipType"] != "AND")
            & (df["RelationshipType"] != "Requires")
            & (df["RelationshipType"] != "Excludes")
        ),
        :,
    ]
    object_property = fm_property.dropna(subset=["RelationshipType"])

    # fill property classes with relationships
    property_dict = {}
    for name, values in dr.set_index("RelationshipType").iteritems():
        property_specs = values.dropna()
        if property_specs.empty:
            print(f"Ignore {name} because no entry was found.")
            continue
        for property_spec in property_specs.index:
            # get dataframe index of object property specification
            idx_element = next(
                iter(
                    object_property.index[
                        object_property["RelationshipType"] == property_spec
                    ]
                )
            )
            # retrieve object property domain and range
            relationship_type = df.loc[idx_element, "RelationshipType"]
            domain_name = df.loc[idx_element, "ContextInformation"]
            range_name = df.loc[idx_element, "RelatedContextInformation"]
            if name not in name2class:
                print(f"Could not find {name}.")
                continue
            # fill property dict and add object property domain and range to class
            property_dict[relationship_type] = create_subclass(
                parent_class=name2class[name],
                name=relationship_type,
            )
            property_dict[relationship_type].domain.append(class_dict[domain_name])
            property_dict[relationship_type].range.append(class_dict[range_name])


def add_comments_to_classes(df, class_dict):
    descriptions = df.dropna(subset=["Description"])
    for _, row in descriptions.iterrows():
        comment = row["Description"]
        relevant_class = row["ContextInformation"]
        class_dict[relevant_class].comment.append(comment)


def add_same_as_class_restriction(df, class_dict):
    same_as = df.dropna(subset=["SameAs"])
    for _, row in same_as.iterrows():
        same = row["SameAs"]
        relevant_class = row["ContextInformation"]
        class_dict[relevant_class].equivalent_to.append(class_dict[same])


def add_disjoint_with_class_restriction(df, class_dict):
    disjoint_with = df.dropna(subset=["DisjointWith"])
    for _, row in disjoint_with.iterrows():
        disjoint = row["DisjointWith"]
        relevant_class = row["ContextInformation"]
        AllDisjoint([class_dict[relevant_class], class_dict[disjoint]])


def main():
    df = pd.read_csv(
        "C://Users/Caesar/Documents/Spaces/BackUp/Dissertation/KontextModellierung/OntoCreationTest_Page_Ontology_FM.csv",
        header=0,
        sep=";",
        encoding="latin1",
    )

    dr = pd.read_csv(
        "C://Users/Caesar/Documents/Spaces/BackUp/Dissertation/KontextModellierung/OntoCreationTest_Page_RelTyp.csv",
        header=0,
        sep=";",
        encoding="latin1",
    )

    con_onto = get_ontology("https://context_ontology/ContextModel.owl")

    with con_onto:
        # create classes according to excel sheet
        class_dict = create_classes_and_subclasses(df)

        # create property classes that define the relationship between classes
        create_relationships_between_classes(df, class_dict, dr)

        # add comments from excel sheet 'Descriptions' to classes
        add_comments_to_classes(df, class_dict)

        # add same as relation to classes
        add_same_as_class_restriction(df, class_dict)

        # add disjoint with relation to classes
        add_disjoint_with_class_restriction(df, class_dict)

        # save ontology to .owl file
        con_onto.save(file="ContextModel.owl", format="rdfxml")


if __name__ == "__main__":
    main()
