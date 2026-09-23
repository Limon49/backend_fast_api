"""
Database access and business rules.

Nothing in this package knows about HTTP: no status codes, no request objects.
That separation is why the purchase logic below can be tested directly, and why
the same function could serve a CLI or a background job later.

Each module answers one question:
``user.py``    who exists
``product.py`` what can be bought
``order.py``   who bought what (the transaction)
``report.py``  the aggregates used by the reports endpoints
"""
