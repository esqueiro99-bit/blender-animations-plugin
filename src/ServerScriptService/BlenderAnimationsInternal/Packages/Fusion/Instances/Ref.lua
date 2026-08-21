
return function(refValue)
    return function(instance)
        if refValue and type(refValue) == "table" and refValue.set then
            refValue:set(instance)
        end
    end
end
