"""
Run this after updating country_info.json and or
"""
import dontmanage


def execute():
	for col in ("field", "doctype"):
		dontmanage.db.sql_ddl(f"alter table `tabSingles` modify column `{col}` varchar(255)")
