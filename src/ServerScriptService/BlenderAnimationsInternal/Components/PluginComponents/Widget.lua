local Fusion = require(script:FindFirstAncestor("BlenderAnimationsInternal").Packages.Fusion)

local Hydrate = Fusion.Hydrate

local COMPONENT_ONLY_PROPERTIES = {
	"Id",
	"InitialDockTo",
	"InitialEnabled",
	"ForceInitialEnabled",
	"FloatingSize",
	"MinimumSize",
	"Plugin"
}

type PluginGuiProperties = {
	Id: string,
	Name: string,
	InitialDockTo: string | Enum.InitialDockState,
	InitialEnabled: boolean,
	ForceInitialEnabled: boolean,
	FloatingSize: Vector2,
	MinimumSize: Vector2,
	Plugin: Plugin, -- Required: the plugin instance
	[any]: any,
}

return function(props: PluginGuiProperties)
	local PluginInstance = props.Plugin
	assert(PluginInstance, "Widget requires a 'Plugin' property to be passed")
	
	local widgetId = props.Id or "BlenderAnimationsMain"
	local dockState = if typeof(props.InitialDockTo) == "string" then Enum.InitialDockState[props.InitialDockTo] else (props.InitialDockTo or Enum.InitialDockState.Right)
	
	local newWidget = PluginInstance:CreateDockWidgetPluginGui(
		widgetId, 
		DockWidgetPluginGuiInfo.new(
			dockState,
			false,
			false,
			props.FloatingSize and props.FloatingSize.X or 300, props.FloatingSize and props.FloatingSize.Y or 600,
			props.MinimumSize and props.MinimumSize.X or 220, props.MinimumSize and props.MinimumSize.Y or 350
		)
	)

	newWidget.Title = props.Name or "Blender Animations"
	newWidget.ZIndexBehavior = Enum.ZIndexBehavior.Sibling

	for _,propertyName in pairs(COMPONENT_ONLY_PROPERTIES) do
		props[propertyName] = nil
	end

	props.Name = nil
	props.Title = nil

	if typeof(props.Enabled) == "table" and props.Enabled.set then
		props.Enabled:set(newWidget.Enabled)
	end

	return Hydrate(newWidget)(props)
end