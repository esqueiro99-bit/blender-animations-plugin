
local Observer = {}
Observer.__index = Observer

function Observer.new(watchedState)
    local self = setmetatable({_state = watchedState, _callbacks = {}}, Observer)
    if watchedState and watchedState._observers then
        watchedState._observers[self] = true
    end
    return self
end

function Observer:_update()
    local val = self._state and self._state:get()
    for _, cb in ipairs(self._callbacks) do
        task.spawn(cb, val)
    end
end


function Observer:onChange(callback)
    table.insert(self._callbacks, callback)
    return function()
        for i, cb in ipairs(self._callbacks) do
            if cb == callback then table.remove(self._callbacks, i) break end
        end
    end
end

function Observer:onBind(callback)
    task.spawn(callback)
    return self:onChange(callback)
end

local mt = getmetatable(Observer) or {}
mt.__call = function(cls, state) return cls.new(state) end
setmetatable(Observer, mt)

return Observer
