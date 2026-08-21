
local Value = {}
Value.__index = Value

function Value.new(initialValue)
    return setmetatable({_value = initialValue, _observers = {}, type = "State", kind = "Value"}, Value)
end


function Value:get()
    return self._value
end

function Value:set(newValue)
    if newValue == self._value then return end
    self._value = newValue
    for obs in pairs(self._observers) do
        task.spawn(obs._update, obs)
    end
end

-- Fusion 0.2 compat: Value() is callable
local mt = getmetatable(Value) or {}
mt.__call = function(cls, v) return cls.new(v) end
setmetatable(Value, mt)

return Value
