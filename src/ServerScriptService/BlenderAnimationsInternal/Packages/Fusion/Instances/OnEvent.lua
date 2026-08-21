
return function(eventName)
    return function(instance, callback)
        instance[eventName]:Connect(callback)
    end
end
