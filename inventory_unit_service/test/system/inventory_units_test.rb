require "application_system_test_case"

class InventoryUnitsTest < ApplicationSystemTestCase
  setup do
    @inventory_unit = inventory_units(:one)
  end

  test "visiting the index" do
    visit inventory_units_url
    assert_selector "h1", text: "Inventory units"
  end

  test "should create inventory unit" do
    visit inventory_units_url
    click_on "New inventory unit"

    click_on "Create Inventory unit"

    assert_text "Inventory unit was successfully created"
    click_on "Back"
  end

  test "should update Inventory unit" do
    visit inventory_unit_url(@inventory_unit)
    click_on "Edit this inventory unit", match: :first

    click_on "Update Inventory unit"

    assert_text "Inventory unit was successfully updated"
    click_on "Back"
  end

  test "should destroy Inventory unit" do
    visit inventory_unit_url(@inventory_unit)
    click_on "Destroy this inventory unit", match: :first

    assert_text "Inventory unit was successfully destroyed"
  end
end
