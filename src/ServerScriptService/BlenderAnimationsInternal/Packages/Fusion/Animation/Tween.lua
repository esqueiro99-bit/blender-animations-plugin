--!native
--!strict
-- Fusion Animation: Tween

local Tween = {}
Tween.__index = Tween

function Tween.new(goalState: any, tweenInfo: TweenInfo?)
    local initialVal = type(goalState) == "table" and goalState.get and goalState:get() or goalState
    local self = setmetatable({
        _goal = goalState,
        _value = initialVal,
        _tweenInfo = tweenInfo,
        _observers = {},
        type = "State",
        kind = "Tween",
    }, Tween)

    if type(goalState) == "table" and goalState._observers then
        local obs = {
            _update = function()
                self._value = goalState:get()
                for o in pairs(self._observers) do
                    task.spawn(o._update, o)
                end
            end
        }
        goalState._observers[obs] = true
    end

    return self
end

function Tween:get()
    if type(self._goal) == "table" and self._goal.get then
        return self._goal:get()
    end
    return self._value
end

local mt = getmetatable(Tween) or {}
mt.__call = function(cls, goalState, tweenInfo)
    return cls.new(goalState, tweenInfo)
end
setmetatable(Tween, mt)

return Tween
