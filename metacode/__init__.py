""" Xerox Metacode (LCDS) parser framework.

Metacode is a low-level, printer-specific order stream whose exact byte encoding
varies by JSL/JDL and target device. This module provides an order-driven parser
that turns a length-prefixed record/order stream into the generic model. The default
order codes (see metacode.parser.ORDERS) are a documented baseline; calibrate them to
your Metacode variant by passing a custom order map. The architecture — orders ->
position/font/text -> model elements — is stable regardless of the specific codes.
"""
