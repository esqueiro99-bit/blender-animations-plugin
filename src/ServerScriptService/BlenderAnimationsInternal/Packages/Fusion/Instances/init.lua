
-- Fusion Instances module
local Children = require(script.Children)
local OnEvent  = require(script.OnEvent)
local OnChange = require(script.OnChange)
local Ref      = require(script.Ref)
local Out      = require(script.Out)
local Cleanup  = require(script.Cleanup)

local SPECIAL_KEYS = {
    [Children] = true,
    [OnEvent]  = true,
    [OnChange] = true,
    [Ref]      = true,
    [Out]      = true,
    [Cleanup]  = true,
}

local Instances = {}

local function applyProps(instance, props)
    local childList = nil
    for key, value in pairs(props) do
        if key == Children then
            childList = value
        elseif type(key) == "function" then
            pcall(key, instance, value)
        elseif type(key) == "string" and key ~= "Parent" then
            if type(value) == "table" and value.get then
                pcall(function() (instance :: any)[key] = value:get() end)
                if value._observers then
                    local obs = {
                        _update = function()
                            pcall(function() (instance :: any)[key] = value:get() end)
                        end
                    }
                    value._observers[obs] = true
                end
            else
                pcall(function() (instance :: any)[key] = value end)
            end
        end
    end

    if childList then
        local currentChildren = {}

        local function clearChildren()
            for _, c in ipairs(currentChildren) do
                if typeof(c) == "Instance" then
                    pcall(function() c:Destroy() end)
                end
            end
            table.clear(currentChildren)
        end

        local function applyChildren(list)
            if type(list) == "table" and list.get then
                list = list:get()
            end
            if type(list) ~= "table" then return end
            for _, child in ipairs(list) do
                if typeof(child) == "Instance" then
                    child.Parent = instance
                    table.insert(currentChildren, child)
                elseif type(child) == "table" then
                    applyChildren(child)
                end
            end
            for k, child in pairs(list) do
                if type(k) ~= "number" and typeof(child) == "Instance" then
                    child.Parent = instance
                    table.insert(currentChildren, child)
                end
            end
        end

        applyChildren(childList)

        if type(childList) == "table" and childList.get and childList._observers then
            local obs = {
                _update = function()
                    clearChildren()
                    applyChildren(childList)
                end
            }
            childList._observers[obs] = true
        end
    end

    -- Set parent last
    if props.Parent then
        pcall(function() instance.Parent = props.Parent end)
    end
end


function Instances.New(className)
    return function(props)
        local instance = Instance.new(className)
        applyProps(instance, props or {})
        return instance
    end
end

function Instances.Hydrate(instance)
    return function(props)
        applyProps(instance, props or {})
        return instance
    end
end

Instances.Children = Children
Instances.OnEvent  = OnEvent
Instances.OnChange = OnChange
Instances.Ref      = Ref
Instances.Out      = Out
Instances.Cleanup  = Cleanup

return Instances
