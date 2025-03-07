class InventoryUnitsController < ApplicationController
  before_action :set_inventory_unit, only: %i[ show edit update destroy ]

  # GET /inventory_units or /inventory_units.json
  def index
    @inventory_units = InventoryUnit.all
  end

  # GET /inventory_units/1 or /inventory_units/1.json
  def show
  end

  # GET /inventory_units/new
  def new
    @inventory_unit = InventoryUnit.new
  end

  # GET /inventory_units/1/edit
  def edit
  end

  # POST /inventory_units or /inventory_units.json
  def create
    @inventory_unit = InventoryUnit.new(params.permit!)

    respond_to do |format|
      if @inventory_unit.save
        # format.html { redirect_to @inventory_unit, notice: "Inventory unit was successfully created." }
        format.json { render :show, status: :created, location: @inventory_unit }
      else
        # format.html { render :new, status: :unprocessable_entity }
        format.json { render json: @inventory_unit.errors, status: :unprocessable_entity }
      end
    end
  end

  # PATCH/PUT /inventory_units/1 or /inventory_units/1.json
  def update
    respond_to do |format|
      if @inventory_unit.update(inventory_unit_params)
        format.html { redirect_to @inventory_unit, notice: "Inventory unit was successfully updated." }
        format.json { render :show, status: :ok, location: @inventory_unit }
      else
        format.html { render :edit, status: :unprocessable_entity }
        format.json { render json: @inventory_unit.errors, status: :unprocessable_entity }
      end
    end
  end

  # DELETE /inventory_units/1 or /inventory_units/1.json
  def destroy
    @inventory_unit.destroy!

    respond_to do |format|
      format.html { redirect_to inventory_units_path, status: :see_other, notice: "Inventory unit was successfully destroyed." }
      format.json { head :no_content }
    end
  end

  private
    # Use callbacks to share common setup or constraints between actions.
    def set_inventory_unit
      @inventory_unit = InventoryUnit.find(params.expect(:id))
    end

    # Only allow a list of trusted parameters through.
    def inventory_unit_params
      params.fetch(:inventory_unit, {})
    end
end
