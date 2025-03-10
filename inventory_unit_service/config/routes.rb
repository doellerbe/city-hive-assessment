Rails.application.routes.draw do
  constraints ->(request) { request.format == :json} do
    resources :inventory_units
  end
end
