-- Written by @boatbomber

local StudioService = game:GetService("StudioService")
local internal = script:FindFirstAncestor("BlenderAnimationsInternal") or script:FindFirstAncestorWhichIsA("Plugin") or script.Parent.Parent.Parent
local Fusion = require(internal:FindFirstChild("Fusion", true) or internal.Packages.Fusion)

local StudioComponents = script.Parent
local StudioComponentsUtil = StudioComponents:FindFirstChild("Util")

local stripProps = require(StudioComponentsUtil.stripProps)
local types = require(StudioComponentsUtil.types)
local unwrap = require(StudioComponentsUtil.unwrap)

local New = Fusion.New
local Hydrate = Fusion.Hydrate
local Computed = Fusion.Computed

type ClassIconProperties = {
	ClassName: (string | types.StateObject<string>),
	[any]: any,
}

local COMPONENT_ONLY_PROPERTIES = {
	"ClassName",
}

return function(props: ClassIconProperties): Frame
	local image = Computed(function()
		local class = unwrap(props.ClassName)
		return StudioService:GetClassIcon(class)
	end)

	local hydrateProps = stripProps(props, COMPONENT_ONLY_PROPERTIES)

	return Hydrate(New "ImageLabel" {
		Name = "ClassIcon:"..props.ClassName,
		Size = UDim2.fromOffset(16, 16),
		BackgroundTransparency = 1,
		Image = Computed(function()
			return unwrap(image).Image
		end),
		ImageRectOffset = Computed(function()
			return unwrap(image).ImageRectOffset
		end),
		ImageRectSize = Computed(function()
			return unwrap(image).ImageRectSize
		end),
	})(hydrateProps)
end
