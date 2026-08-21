
return function(propertyName)
    return function(instance, outValue)
        if outValue and type(outValue) == "table" and outValue.set then
            outValue:set(instance[propertyName])
            instance:GetPropertyChangedSignal(propertyName):Connect(function()
                outValue:set(instance[propertyName])
            end)
        end
    end
end
