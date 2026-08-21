--!native
--!strict
--!optimize 2

local State = require(script.Parent.Parent.Parent.state)
local Fusion = require(script.Parent.Parent.Parent.Packages.Fusion)

local New = Fusion.New
local Children = Fusion.Children
local Computed = Fusion.Computed
local Value = Fusion.Value
local OnEvent = Fusion.OnEvent
local Observer = Fusion.Observer

local StudioComponents = script.Parent.Parent.Parent.Components:FindFirstChild("StudioComponents")
local StudioComponentsUtil = StudioComponents:FindFirstChild("Util")
local themeProvider = require(StudioComponentsUtil.themeProvider)
local Label = require(StudioComponents.Label)
local Button = require(StudioComponents.Button)
local VerticalCollapsibleSection = require(StudioComponents.VerticalCollapsibleSection)

local DecalControls = {}

-- Safely call rigManager methods
local function callRigManager(method: string, ...)
	local rm = State.rigManager
	if rm and type(rm[method]) == "function" then
		local ok, err = pcall(rm[method], rm, ...)
		if not ok then
			warn("[DecalControls] rigManager:" .. method .. " error: " .. tostring(err))
		end
	end
end

-- Creates the scrollable grid of decal buttons dynamically
local function buildDecalButtons(container: Frame, services: any)
	-- clear existing
	for _, child in ipairs(container:GetChildren()) do
		if child:IsA("TextButton") or child:IsA("UIGridLayout") then
			child:Destroy()
		end
	end

	local names = State.decalNames:get()
	if #names == 0 then
		return
	end

	-- Grid layout
	local grid = Instance.new("UIGridLayout")
	grid.CellPadding = UDim2.new(0, 4, 0, 4)
	grid.CellSize = UDim2.new(0, 52, 0, 24)
	grid.FillDirection = Enum.FillDirection.Horizontal
	grid.SortOrder = Enum.SortOrder.LayoutOrder
	grid.Parent = container

	for i, decalName in ipairs(names) do
		-- shorten the label: "Face.1" -> "F.1", else first 5 chars
		local shortName = decalName:gsub("Face%.", "F.")
		if shortName == decalName then
			shortName = decalName:sub(1, 5)
		end

		local isActive = State.activeDecals:get()[decalName] ~= false

		local btn = Instance.new("TextButton")
		btn.LayoutOrder = i
		btn.Size = UDim2.new(0, 52, 0, 24)
		btn.BackgroundColor3 = isActive
			and Color3.fromRGB(0, 120, 212)   -- blue = ON
			or themeProvider:GetColor(Enum.StudioStyleGuideColor.MainButton)
		btn.TextColor3 = themeProvider:GetColor(Enum.StudioStyleGuideColor.MainText)
		btn.Font = Enum.Font.GothamSemibold
		btn.TextSize = 11
		btn.Text = shortName
		btn.BorderSizePixel = 0
		btn.AutoButtonColor = false

		local corner = Instance.new("UICorner")
		corner.CornerRadius = UDim.new(0, 4)
		corner.Parent = btn

		btn.MouseButton1Click:Connect(function()
			callRigManager("toggleDecal", decalName)
			-- update button color immediately
			local nowActive = State.activeDecals:get()[decalName] ~= false
			btn.BackgroundColor3 = nowActive
				and Color3.fromRGB(0, 120, 212)
				or themeProvider:GetColor(Enum.StudioStyleGuideColor.MainButton)
		end)

		btn.Parent = container
	end
end

function DecalControls.createDecalControlsUI(services: any, layoutOrder: number?)

	-- Inner scrollable frame that holds the buttons
	local buttonsFrame = New("Frame")({
		Name = "DecalButtonsGrid",
		Size = UDim2.new(1, -16, 0, 0),
		AutomaticSize = Enum.AutomaticSize.Y,
		BackgroundTransparency = 1,
		LayoutOrder = 2,
	})

	-- Action buttons row
	local function makeActionBtn(text: string, lo: number, onClick: () -> ())
		local b = Instance.new("TextButton")
		b.LayoutOrder = lo
		b.Size = UDim2.new(0, 80, 0, 22)
		b.Text = text
		b.Font = Enum.Font.Gotham
		b.TextSize = 11
		b.BorderSizePixel = 0
		b.BackgroundColor3 = themeProvider:GetColor(Enum.StudioStyleGuideColor.MainButton)
		b.TextColor3 = themeProvider:GetColor(Enum.StudioStyleGuideColor.MainText)
		b.AutoButtonColor = true
		local c = Instance.new("UICorner")
		c.CornerRadius = UDim.new(0, 4)
		c.Parent = b
		b.MouseButton1Click:Connect(onClick)
		return b
	end

	local actionsRow = New("Frame")({
		Name = "DecalActions",
		LayoutOrder = 3,
		Size = UDim2.new(1, -16, 0, 30),
		BackgroundTransparency = 1,
		[Children] = {
			New("UIListLayout")({
				FillDirection = Enum.FillDirection.Horizontal,
				VerticalAlignment = Enum.VerticalAlignment.Center,
				Padding = UDim.new(0, 6),
				SortOrder = Enum.SortOrder.LayoutOrder,
			}),
			makeActionBtn("All ON", 1, function()
				callRigManager("setAllDecals", true)
			end),
			makeActionBtn("All OFF", 2, function()
				callRigManager("setAllDecals", false)
			end),
			makeActionBtn("Rescan", 3, function()
				if State.activeRigModel then
					callRigManager("scanRigDecals", State.activeRigModel)
				end
			end),
		},
	})

	local statusLabel = New("TextLabel")({
		LayoutOrder = 1,
		Size = UDim2.new(1, -16, 0, 20),
		BackgroundTransparency = 1,
		TextColor3 = themeProvider:GetColor(Enum.StudioStyleGuideColor.SubText),
		Font = Enum.Font.Gotham,
		TextSize = 11,
		TextXAlignment = Enum.TextXAlignment.Left,
		Text = Computed(function()
			local names = State.decalNames:get()
			if #names == 0 then
				return "No Decals found on Head. Select a rig."
			end
			return string.format("Found %d Head Decal(s):", #names)
		end),
	})

	local inner = New("Frame")({
		Name = "DecalInner",
		Size = UDim2.new(1, 0, 0, 0),
		AutomaticSize = Enum.AutomaticSize.Y,
		BackgroundTransparency = 1,
		[Children] = {
			New("UIListLayout")({
				FillDirection = Enum.FillDirection.Vertical,
				Padding = UDim.new(0, 4),
				SortOrder = Enum.SortOrder.LayoutOrder,
			}),
			New("UIPadding")({
				PaddingLeft = UDim.new(0, 8),
				PaddingRight = UDim.new(0, 8),
				PaddingTop = UDim.new(0, 4),
				PaddingBottom = UDim.new(0, 4),
			}),
			statusLabel,
			buttonsFrame,
			actionsRow,
		},
	})

	-- Build buttons initially
	task.defer(function()
		pcall(buildDecalButtons, buttonsFrame, services)
	end)

	-- Re-build buttons whenever decalNames changes
	local disconnectObserver: (() -> ())?
	if Observer and type(Observer) == "function" then
		local obs = Observer(State.decalNames)
		disconnectObserver = obs:onChange(function()
			task.defer(function()
				pcall(buildDecalButtons, buttonsFrame, services)
			end)
		end)
	end

	local section = VerticalCollapsibleSection({
		Text = "Decal Expressions",
		Collapsed = false,
		LayoutOrder = layoutOrder or 3,
		[Children] = { inner },
	})

	return section
end

return DecalControls
