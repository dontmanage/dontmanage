import dontmanage


def execute():
	"""Remove stale docfields from legacy version"""
	dontmanage.db.delete("DocField", {"options": "Data Import", "parent": "Data Import Legacy"})
