
return function(stateOrTable, processor, destructor)
    local result = {}
    local src = type(stateOrTable) == "table" and stateOrTable.get and stateOrTable:get() or stateOrTable
    if type(src) == "table" then
        for k, v in pairs(src) do
            local ok, nk = pcall(processor, k)
            if ok and nk ~= nil then result[nk] = v end
        end
    end
    return result
end
