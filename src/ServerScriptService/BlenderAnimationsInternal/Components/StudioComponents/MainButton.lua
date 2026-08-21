-- Roact version by @sircfenner
-- Ported to Fusion by @YasuYoshida

local internal = script:FindFirstAncestor("BlenderAnimationsInternal") or script:FindFirstAncestorWhichIsA("Plugin") or script.Parent.Parent.Parent
local Fusion = require(internal:FindFirstChild("Fusion", true) or internal.Packages.Fusion)

local StudioComponents = script.Parent
local StudioComponentsUtil = StudioComponents:FindFirstChild("Util")

local Button = require(StudioComponents.Button)

local Children = Fusion.Children
local Hydrate = Fusion.Hydrate
local New = Fusion.New

local baseProperties = {
	TextColorStyle = Enum.StudioStyleGuideColor.DialogMainButtonText,
	BackgroundColorStyle = Enum.StudioStyleGuideColor.DialogMainButton,
	BorderColorStyle = Enum.StudioStyleGuideColor.ButtonBorder,
	Name = "MainButton",
}

return function(props: Button.ButtonProperties): TextButton
	for index,value in pairs(baseProperties) do
		if props[index]==nil then
			props[index] = value
		end
	end
	return Button(props)
end