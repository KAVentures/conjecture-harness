# Polynomial regression evidence

Local command: python -m unittest discover -s tests -v

Ran 109 tests in 14.045s — OK. Fifteen new tests cover coefficient identities, quadratic and quartic squares, orthant restrictions, exact counterexamples, tampered certificates, invalid inputs, unknown Motzkin control, target binding, auxiliary refutation, automatic runner discharge and reserved evidence IDs. A first quartic test exposed an overly restrictive Gram choice; negative even cross terms are now allowed as off-diagonal terms. No live-model or novel-discovery claim.

Follow-up: exposed canonical solver syntax in the model prompt and added one regression. Ran 110 tests in 14.618s — OK. No authenticated model call was made.
