<template>
  <q-dialog
    ref="dialogRef"
    @hide="onDialogHide"
  >
    <q-card style="min-width: 300px">
      <q-form
        @reset="onDialogCancel"
        @submit="onSubmit"
      >
        <q-card-section class="text-h6">
          <template v-if="mode === 'create'">Create Balloon</template>
          <template v-else> Edit Balloon</template>
        </q-card-section>

        <q-card-section class="q-pt-none q-gutter-y-md">
          <q-input
            v-model="name"
            label="Name"
            lazy-rules
            :rules="[
              (val?: string | null) =>
                (!!val && val.length > 0) || 'Name is required.',
              (val?: string | null) =>
                nameIsUnique(val) || 'Name must be unique.',
            ]"
            hide-bottom-space
            rounded
            outlined
          />

          <q-input
            v-model.number="maxCapacity"
            type="number"
            label="Maximum Capacity"
            hint="Including the pilot"
            lazy-rules
            :rules="[
              (val?: number | null) =>
                (!!val && val > 0) || 'Maximum Capacity is required.',
            ]"
            rounded
            outlined
          />

          <q-input
            v-model.number="maxWeight"
            type="number"
            label="Maximum Weight"
            hint="Optional"
            suffix=" kg"
            lazy-rules
            :rules="[
              (val?: number | null) =>
                !val || val > 0 || 'Max weight must be greater than 0.',
            ]"
            clearable
            rounded
            outlined
          />

          <q-select
            v-model="allowedOperatorIds"
            label="Allowed operators"
            use-input
            use-chips
            multiple
            input-debounce="0"
            :options="filterOptions"
            emit-value
            map-options
            @filter="filterFn"
            outlined
            rounded
          />
        </q-card-section>

        <q-card-actions
          align="right"
          class="text-primary"
        >
          <q-btn
            label="Cancel"
            type="reset"
            color="primary"
            rounded
            outline
          />
          <q-btn
            :label="mode === 'create' ? 'Create' : 'Save'"
            type="submit"
            color="primary"
            rounded
          />
        </q-card-actions>
      </q-form>
    </q-card>
  </q-dialog>
</template>

<script lang="ts" setup>
import { computed, ref, toRaw } from 'vue';
import type { Person, Balloon } from 'app/src-common/entities';
import { useDialogPluginComponent, type QSelectOption } from 'quasar';

const { dialogRef, onDialogHide, onDialogOK, onDialogCancel } =
  useDialogPluginComponent();

const { people, balloon, existingNames } = defineProps<{
  balloon?: Balloon;
  existingNames?: string[];
  people: Person[];
}>();

defineEmits([...useDialogPluginComponent.emits]);

const name = ref<string | undefined>(balloon?.name);
const maxCapacity = ref<number | undefined>(balloon?.maxCapacity);
const maxWeight = ref<number | undefined>(balloon?.maxWeight);
const allowedOperatorIds = ref<string[]>(balloon?.allowedOperatorIds ?? []);

const operatorOptions = computed<QSelectOption[]>(() => {
  return people
    .filter((value) => value.role === 'counselor')
    .toSorted((a, b) => a.name.localeCompare(b.name))
    .map((value) => ({
      label: value.name,
      value: value.id,
    }));
});

const filterOptions = ref<QSelectOption[]>(operatorOptions.value);

const mode = computed<'create' | 'edit'>(() => {
  return balloon ? 'edit' : 'create';
});

function onSubmit() {
  const payload: Omit<Balloon, 'id'> = {
    type: 'balloon',
    name: toRaw(name.value).trim(),
    maxCapacity: toRaw(maxCapacity.value),
    maxWeight: toRaw(maxWeight.value) ?? undefined,
    allowedOperatorIds: toRaw(allowedOperatorIds.value),
  };

  onDialogOK(payload);
}

function filterFn(val: string, update: (a: () => void) => void) {
  update(() => {
    const needle = val.toLowerCase();
    filterOptions.value = operatorOptions.value.filter(
      (value) => value.label.toLowerCase().indexOf(needle) > -1,
    );
  });
}

function nameIsUnique(name: string): boolean {
  name = name.trim().toLowerCase();
  if (name === balloon?.name.toLowerCase()) {
    return true;
  }

  return !existingNames?.some((existingName) => {
    return existingName.toLowerCase() === name;
  });
}
</script>

<style scoped></style>
