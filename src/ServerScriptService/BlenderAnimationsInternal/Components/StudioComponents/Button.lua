-- Roact version by @sircfenner
-- Ported to Fusion by @YasuYoshida

local internal = script:FindFirstAncestor("BlenderAnimationsInternal") or script:FindFirstAncestorWhichIsA("Plugin") or script.Parent.Parent.Parent
local Fusion = require(internal:FindFirstChild("Fusion", true) or internal.Packages.Fusion)

local StudioComponents = script.Parent
local StudioComponentsUtil = StudioComponents:FindFirstChild("Util")

local BaseButton = require(StudioComponents.BaseButton)

local New = Fusion.New
local Children = Fusion.Children
local Hydrate = Fusion.Hydrate

export type ButtonProperties = BaseButton.BaseButtonProperties

return function(props: ButtonProperties): TextButton
	if not props.Name then
		props.Name = "Button"
	end

	local newButton = BaseButton(props)
	return newButton
end
