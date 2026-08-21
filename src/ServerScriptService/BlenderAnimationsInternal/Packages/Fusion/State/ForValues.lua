
return function(stateOrTable, processor, destructor)
    local result = {}
    local src = type(stateOrTable) == "table" and stateOrTable.get and stateOrTable:get() or stateOrTable
    if type(src) == "table" then
        for k, v in pairs(src) do
            local ok, nv = pcall(processor, v)
            if ok and nv ~= nil then result[k] = nv end
        end
    end
    return result
end
