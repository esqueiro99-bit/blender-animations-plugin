
return function(value)
    local t = typeof(value)
    if t == "table" then
        local mt = getmetatable(value)
        if type(mt) == "table" and mt.__type then
            return mt.__type
        end
    end
    return t
end
