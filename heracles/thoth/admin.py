from django.contrib import admin

from . import models as m

class BookingAdmin(admin.ModelAdmin):
    pass
admin.site.register(m.Booking, BookingAdmin)

class BookingPartAdmin(admin.ModelAdmin):
    pass
admin.site.register(m.BookingPart, BookingPartAdmin)

class LendablesOwnerAdmin(admin.ModelAdmin):
    pass
admin.site.register(m.LendablesOwner, LendablesOwnerAdmin)

class LendableTypeAdmin(admin.ModelAdmin):
    pass
admin.site.register(m.LendableType, LendableTypeAdmin)

class LendableAdmin(admin.ModelAdmin):
    pass
admin.site.register(m.Lendable, LendableAdmin)

