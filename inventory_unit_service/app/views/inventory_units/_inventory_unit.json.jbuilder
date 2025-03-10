# Remove route params from response
json.merge! inventory_unit.attributes.except("action", "controller", "format", "inventory_unit")
