
-- Promise 4.0.0 (minimal compatible version)
-- https://github.com/evaera/roblox-lua-promise
local Promise = {}
Promise.__index = Promise

Promise.Status = {
    Started = "Started",
    Resolved = "Resolved",
    Rejected = "Rejected",
    Cancelled = "Cancelled",
}

function Promise.new(executor)
    local self = setmetatable({
        _status = Promise.Status.Started,
        _value = nil,
        _callbacks = {},
    }, Promise)
    local function resolve(...)
        if self._status ~= Promise.Status.Started then return end
        self._status = Promise.Status.Resolved
        self._value = {...}
        for _, cb in ipairs(self._callbacks) do
            if cb.type == "resolve" then task.spawn(cb.fn, ...) end
        end
    end
    local function reject(...)
        if self._status ~= Promise.Status.Started then return end
        self._status = Promise.Status.Rejected
        self._value = {...}
        for _, cb in ipairs(self._callbacks) do
            if cb.type == "reject" then task.spawn(cb.fn, ...) end
        end
    end
    task.spawn(executor, resolve, reject)
    return self
end

function Promise.resolve(...)
    local args = {...}
    return Promise.new(function(resolve) resolve(table.unpack(args)) end)
end

function Promise.reject(...)
    local args = {...}
    return Promise.new(function(_, reject) reject(table.unpack(args)) end)
end

function Promise:andThen(onFulfilled, onRejected)
    return Promise.new(function(resolve, reject)
        if self._status == Promise.Status.Resolved then
            task.spawn(function()
                if onFulfilled then
                    local ok, result = pcall(onFulfilled, table.unpack(self._value or {}))
                    if ok then resolve(result) else reject(result) end
                else
                    resolve(table.unpack(self._value or {}))
                end
            end)
        elseif self._status == Promise.Status.Rejected then
            task.spawn(function()
                if onRejected then
                    local ok, result = pcall(onRejected, table.unpack(self._value or {}))
                    if ok then resolve(result) else reject(result) end
                else
                    reject(table.unpack(self._value or {}))
                end
            end)
        else
            table.insert(self._callbacks, {type="resolve", fn=function(...)
                if onFulfilled then
                    local ok, result = pcall(onFulfilled, ...)
                    if ok then resolve(result) else reject(result) end
                else resolve(...) end
            end})
            table.insert(self._callbacks, {type="reject", fn=function(...)
                if onRejected then
                    local ok, result = pcall(onRejected, ...)
                    if ok then resolve(result) else reject(result) end
                else reject(...) end
            end})
        end
    end)
end

function Promise:catch(onRejected)
    return self:andThen(nil, onRejected)
end

function Promise:finally(fn)
    return self:andThen(function(...) fn() return ... end, function(...) fn() return ... end)
end

function Promise:await()
    if self._status == Promise.Status.Resolved then
        return true, table.unpack(self._value or {})
    elseif self._status == Promise.Status.Rejected then
        return false, table.unpack(self._value or {})
    end
    -- spin wait (last resort)
    while self._status == Promise.Status.Started do
        task.wait()
    end
    if self._status == Promise.Status.Resolved then
        return true, table.unpack(self._value or {})
    else
        return false, table.unpack(self._value or {})
    end
end

return Promise
