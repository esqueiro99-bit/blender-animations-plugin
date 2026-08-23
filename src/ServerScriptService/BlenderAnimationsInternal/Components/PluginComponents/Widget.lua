local Fusion = require(script:FindFirstAncestor("BlenderAnimationsInternal").Packages.Fusion)

local Hydrate = Fusion.Hydrate
local Observer = Fusion.Observer

local COMPONENT_ONLY_PROPERTIES = {
	"Id",
	"InitialDockTo",
	"InitialEnabled",
	"ForceInitialEnabled",
	"FloatingSize",
	"MinimumSize",
	"Plugin",
	"Enabled", -- we handle Enabled manually below
}

type PluginGuiProperties = {
	Id: string,
	Name: string,
	InitialDockTo: string | Enum.InitialDockState,
	InitialEnabled: boolean,
	ForceInitialEnabled: boolean,
	FloatingSize: Vector2,
	MinimumSize: Vector2,
	Plugin: Plugin,
	[any]: any,
}

local function unwrap(value: any): any
	if typeof(value) == "table" and value.get then
		return value:get()
	end
	return value
end

return function(props: PluginGuiProperties)
	local PluginInstance = props.Plugin
	assert(PluginInstance, "Widget requires a 'Plugin' property to be passed")

	local widgetId = props.Id or "BlenderAnimationsMain"
	local dockState = if typeof(props.InitialDockTo) == "string"
		then Enum.InitialDockState[props.InitialDockTo]
		else (props.InitialDockTo or Enum.InitialDockState.Right)

	local newWidget = PluginInstance:CreateDockWidgetPluginGui(
		widgetId,
		DockWidgetPluginGuiInfo.new(
			dockState,
			false, -- InitialEnabled
			false, -- ForceInitialEnabled
			props.FloatingSize and props.FloatingSize.X or 300,
			props.FloatingSize and props.FloatingSize.Y or 600,
			props.MinimumSize and props.MinimumSize.X or 220,
			props.MinimumSize and props.MinimumSize.Y or 350
		)
	)

	newWidget.Title = props.Name or "Blender Animations"
	newWidget.ZIndexBehavior = Enum.ZIndexBehavior.Sibling

	-- Handle Enabled reactivity manually:
	-- If a Fusion Value/State is passed, observe it and push changes into the widget directly.
	local enabledProp = props.Enabled
	if typeof(enabledProp) == "table" and enabledProp.get then
		-- Initial apply (don't sync widget -> state, only state -> widget)
		newWidget.Enabled = unwrap(enabledProp)
		-- Watch for future changes and apply them to the real DockWidget
		local obs = Observer(enabledProp)
		PluginInstance.Unloading:Connect(obs:onChange(function()
			local v = unwrap(enabledProp)
			if newWidget.Enabled ~= v then
				newWidget.Enabled = v
			end
		end))
	end

	-- Build hydrate props without Enabled and other special keys
	local hydrateProps = {}
	for k, v in pairs(props) do
		local skip = false
		for _, name in ipairs(COMPONENT_ONLY_PROPERTIES) do
			if k == name then skip = true; break end
		end
		if k ~= "Name" and k ~= "Title" and not skip then
			hydrateProps[k] = v
		end
	end

	return Hydrate(newWidget)(hydrateProps)
end