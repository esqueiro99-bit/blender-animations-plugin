
return function(t, name)
    return setmetatable({}, {
        __index = t,
        __newindex = function(_, k, v)
            error(name .. " is read-only", 2)
        end,
    })
end
