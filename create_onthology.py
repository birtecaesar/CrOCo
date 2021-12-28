import pandas as pd
from owlready2 import ObjectProperty, Thing, get_ontology

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


def create_relationships_between_classes(df, class_dict):
    object_property = df.dropna(subset=["RelationshipType"])
    property_dict = {}
    for _, row in object_property.iterrows():
        relationship_type = row["RelationshipType"]
        domain_name = row["ContextInformation"]
        range_name = row["RelatedContextInformation"]
        property_dict[relationship_type] = create_subclass(
            parent_class=ObjectProperty,
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


def main():
    df = pd.read_excel(
        "C://Users/Caesar/Documents/Spaces/BackUp/Dissertation/KontextModellierung/OntoCreationTest.xlsx",
        sheet_name=1,
    )

    con_onto = get_ontology("https://context_ontology/Normnummer.owl")

    with con_onto:
        # create classes according to excel sheet
        class_dict = create_classes_and_subclasses(df)

        # create property classes that define the relationship between classes
        create_relationships_between_classes(df, class_dict)

        # add comments from excel sheet 'Descriptions' to classes
        add_comments_to_classes(df, class_dict)

        # save onthology to .owl file
        con_onto.save(file="Normnummer.owl", format="rdfxml")


if __name__ == "__main__":
    main()
