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
        <q-card-section class="text-h6"> Smart Fill </q-card-section>

        <q-card-section class="q-pt-none q-gutter-y-md">
          <q-select
            v-model="options.leg"
            label="Flight Leg"
            :options="flightLegOptions"
            emit-value
            map-options
            outlined
            rounded
          />

          <q-expansion-item label="Advanced Options">
            <div class="column q-gutter-sm">
              <q-input
                v-model="options.wPassengerFairness"
                label="Passenger Fairness Weight"
                type="number"
                dense
                outlined
                rounded
              />
              <q-input
                v-if="options.leg != null"
                v-model="options.wSecondLegFairness"
                label="Second Leg Fairness Weight"
                type="number"
                dense
                outlined
                rounded
              />
              <q-input
                v-model="options.wPilotFairness"
                label="Pilot Fairness Weight"
                type="number"
                dense
                outlined
                rounded
              />
              <q-input
                v-model="options.wVehicleRotation"
                label="Vehicle Rotation Weight"
                type="number"
                dense
                outlined
                rounded
              />
              <q-input
                v-model="options.wNationalityDiversity"
                label="Nationality Diversity Weight"
                type="number"
                dense
                outlined
                rounded
              />
              <q-input
                v-model="options.timeLimit"
                label="Time Limit (seconds)"
                type="number"
                dense
                outlined
                rounded
              />
            </div>
          </q-expansion-item>
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
            label="Smart Fill"
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
import { reactive, toRaw } from 'vue';
import { useDialogPluginComponent } from 'quasar';
import type { SmartFillOptions } from 'app/src-common/entities';

const { dialogRef, onDialogHide, onDialogOK, onDialogCancel } =
  useDialogPluginComponent();

defineEmits([...useDialogPluginComponent.emits]);

const options = reactive<SmartFillOptions>({
  leg: null,
});

const flightLegOptions = [
  { label: 'None', value: null },
  { label: 'First', value: 'first' },
  { label: 'Second', value: 'second' },
];

function onSubmit() {
  onDialogOK(toRaw(options));
}
</script>

<style scoped></style>
