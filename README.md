# CrOCo
## **Cr**eate **O**ntologies for **Co**ntext description of systems from a predefined csv sheet

CrOCo helps develop context models for reconfigurable systems by utilizing community information resources for improved model reusability. 
Using the provided template CrOCo generate ontology Tboxes including object properties.

To create the ontology [Owlready2](https://github.com/pwin/owlready2), a package for manipulating OWL 2.0 ontologies in Python.
The ontology is saved in RDF/XML format, which is readable by representative graph management tools like Protégé or GraphDB.
If existing ontology design patterns are used, these are imported first (1). 
Afterwards the new concepts are created based on the csv's (2).

If using CrOCo, please cite accordingly:
_B. Caesar, A. Valdezate, J. Ladiges, R. Capilla and A. Fay, "A Process for Identifying and Modeling Relevant System Context for the Reconfiguration of Automated Systems," in IEEE Transactions on Automation Science and Engineering, doi: [10.1109/TASE.2023.3291394](https://doi.org/10.1109/TASE.2023.3291394)._
