
return function(value)
    if type(value) == "table" and value.get then
        return value:get()
    end
    return value
end
