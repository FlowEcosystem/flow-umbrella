import { useAdminsStore } from '@/domains/admins/store'
import { useAuthStore }   from '@/domains/auth/store'
import { useToast }       from '@/shared/composables/useToast'
import { usePagination }  from '@/shared/composables/usePagination'
import { ADMIN_ROLES }    from '@/domains/admins/admins.utils'

export function useAdminsPage() {
  const store = useAdminsStore()
  const auth  = useAuthStore()
  const toast = useToast()

  onMounted(() => store.fetch())

  // ── filter ────────────────────────────────────────────────
  const searchQuery = ref('')

  const filteredAdmins = computed(() => {
    const q = searchQuery.value.trim().toLowerCase()
    if (!q) return store.items
    return store.items.filter(a =>
      a.email.toLowerCase().includes(q) ||
      (a.full_name ?? '').toLowerCase().includes(q)
    )
  })

  const hasFilters = computed(() => !!searchQuery.value.trim())
  function resetFilters() { searchQuery.value = '' }

  const { page, totalPages, paged: pagedAdmins, goTo } = usePagination(filteredAdmins, 25)

  // ── form dialog (create + edit) ───────────────────────────
  const formOpen    = ref(false)
  const formTarget  = ref(null)
  const formData    = ref({ email: '', password: '', full_name: '', role: 'admin' })
  const formLoading = ref(false)
  const formError   = ref('')

  const isEdit = computed(() => !!formTarget.value)

  function openCreate() {
    formTarget.value = null
    formData.value   = { email: '', password: '', full_name: '', role: 'admin' }
    formError.value  = ''
    formOpen.value   = true
  }

  function openEdit(admin) {
    formTarget.value = admin
    formData.value   = { email: admin.email, full_name: admin.full_name ?? '', role: admin.role, is_active: admin.is_active }
    formError.value  = ''
    formOpen.value   = true
  }

  async function submitForm() {
    formLoading.value = true
    formError.value   = ''
    try {
      if (isEdit.value) {
        const payload = {
          email:     formData.value.email     || undefined,
          full_name: formData.value.full_name || null,
          role:      formData.value.role      || undefined,
          is_active: formData.value.is_active,
        }
        await store.update(formTarget.value.id, payload)
        toast.success('Администратор обновлён')
      } else {
        await store.create({
          email:     formData.value.email,
          password:  formData.value.password,
          full_name: formData.value.full_name || null,
          role:      formData.value.role,
        })
        toast.success('Администратор создан')
      }
      formOpen.value = false
    } catch (err) {
      formError.value = err.message ?? 'Ошибка сохранения'
    } finally {
      formLoading.value = false
    }
  }

  // ── delete ────────────────────────────────────────────────
  const deleteTarget  = ref(null)
  const deleteLoading = ref(false)

  function openDelete(admin)  { deleteTarget.value = admin }
  function closeDelete()      { deleteTarget.value = null  }

  async function confirmDelete() {
    if (!deleteTarget.value) return
    deleteLoading.value = true
    try {
      await store.remove(deleteTarget.value.id)
      toast.success('Администратор удалён')
      deleteTarget.value = null
    } catch (err) {
      toast.error(err.message ?? 'Ошибка удаления')
      deleteTarget.value = null
    } finally {
      deleteLoading.value = false
    }
  }

  const isSelf = (admin) => admin.id === auth.currentUser?.id

  return {
    store, auth,
    filteredAdmins, pagedAdmins, page, totalPages, goTo,
    searchQuery, hasFilters, resetFilters,
    formOpen, formTarget, formData, formLoading, formError,
    isEdit, openCreate, openEdit, submitForm,
    deleteTarget, deleteLoading, openDelete, closeDelete, confirmDelete,
    isSelf, ADMIN_ROLES,
  }
}
