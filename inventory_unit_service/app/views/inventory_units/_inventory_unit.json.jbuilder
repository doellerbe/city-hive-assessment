# json.extract! inventory_unit, :id, :inventory_unit, :created_at, :updated_at
# Extract all fields
json.merge! inventory_unit.attributes.except("controller", "format", "inventory_unit")
# json.url inventory_unit_url(inventory_unit, format: :json)
