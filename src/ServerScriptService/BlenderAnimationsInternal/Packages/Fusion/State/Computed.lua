
local Computed = {}
Computed.__index = Computed

function Computed.new(fn)
    local self = setmetatable({_fn = fn, _value = nil, _observers = {}}, Computed)
    local ok, v = pcall(fn)
    self._value = ok and v or nil
    return self
end

function Computed:get()
    local ok, v = pcall(self._fn)
    return ok and v or self._value
end

local mt = getmetatable(Computed) or {}
mt.__call = function(cls, fn) return cls.new(fn) end
setmetatable(Computed, mt)

return Computed
