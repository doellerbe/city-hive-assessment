# Remove route params from response
json.merge! inventory_unit.attributes.except("action", "controller", "format", "inventory_unit")
json.batch_id SecureRandom.uuid
json.number_of_units @inventory_units.size()
