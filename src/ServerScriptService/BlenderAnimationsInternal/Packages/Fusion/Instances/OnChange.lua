
return function(propertyName)
    return function(instance, callback)
        instance:GetPropertyChangedSignal(propertyName):Connect(callback)
    end
end
