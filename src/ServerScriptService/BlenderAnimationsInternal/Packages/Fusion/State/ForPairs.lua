
return function(stateOrTable, processor, destructor)
    -- Returns a reactive table-like object; simplified for compatibility
    local result = {}
    local src = type(stateOrTable) == "table" and stateOrTable.get and stateOrTable:get() or stateOrTable
    if type(src) == "table" then
        for k, v in pairs(src) do
            local ok, nk, nv = pcall(processor, k, v)
            if ok and nk ~= nil then result[nk] = nv end
        end
    end
    return result
end
