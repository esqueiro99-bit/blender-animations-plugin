--!native
--!strict
-- Fusion Animation: Spring

local Spring = {}
Spring.__index = Spring

function Spring.new(goalState: any, speed: number?, damping: number?)
    local initialVal = type(goalState) == "table" and goalState.get and goalState:get() or goalState
    local self = setmetatable({
        _goal = goalState,
        _value = initialVal,
        _speed = speed or 10,
        _damping = damping or 1,
        _observers = {},
        type = "State",
        kind = "Spring",
    }, Spring)

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

function Spring:get()
    if type(self._goal) == "table" and self._goal.get then
        return self._goal:get()
    end
    return self._value
end

function Spring:set(newGoal: any)
    if type(self._goal) == "table" and self._goal.set then
        self._goal:set(newGoal)
    else
        self._value = newGoal
    end
end

local mt = getmetatable(Spring) or {}
mt.__call = function(cls, goalState, speed, damping)
    return cls.new(goalState, speed, damping)
end
setmetatable(Spring, mt)

return Spring
