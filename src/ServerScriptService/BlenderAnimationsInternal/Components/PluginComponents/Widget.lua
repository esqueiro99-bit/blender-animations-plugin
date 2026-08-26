local Fusion = require(script:FindFirstAncestor("BlenderAnimationsInternal").Packages.Fusion)

local Hydrate = Fusion.Hydrate

local COMPONENT_ONLY_PROPERTIES = {
	"Id",
	"InitialDockTo",
	"InitialEnabled",
	"ForceInitialEnabled",
	"FloatingSize",
	"MinimumSize",
	"Plugin",
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
			false,
			false,
			props.FloatingSize and props.FloatingSize.X or 300,
			props.FloatingSize and props.FloatingSize.Y or 600,
			props.MinimumSize and props.MinimumSize.X or 220,
			props.MinimumSize and props.MinimumSize.Y or 350
		)
	)

	newWidget.Title = props.Name or "Blender Animations"
	newWidget.ZIndexBehavior = Enum.ZIndexBehavior.Sibling

	-- Remove special props that DockWidgetPluginGui doesn't accept
	-- We strip Enabled too — caller manages it directly on the returned instance
	for _, propertyName in ipairs(COMPONENT_ONLY_PROPERTIES) do
		props[propertyName] = nil
	end
	props.Name = nil
	props.Title = nil
	props.Enabled = nil  -- caller sets widget.Enabled directly; don't let Fusion fight us

	-- Hydrate remaining props (Children, ZIndexBehavior, etc.) onto the widget
	return Hydrate(newWidget)(props)
end