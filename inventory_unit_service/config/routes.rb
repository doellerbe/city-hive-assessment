Rails.application.routes.draw do
  constraints ->(request) { request.format == :json} do
    resources :inventory_units
  end
  # root to: redirect('/inventory_units#index')
end
