/*
 * Copyright 2015-present Open Networking Foundation
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package org.onosproject.vtn.cli;

import org.apache.karaf.shell.commands.Command;
import org.apache.karaf.shell.commands.Option;
import org.onlab.osgi.DefaultServiceDirectory;
import org.onlab.osgi.ServiceDirectory;
import org.onosproject.cli.AbstractShellCommand;
import org.onosproject.net.Device;
import org.onosproject.net.DeviceId;
import org.onosproject.net.device.DeviceService;
import org.onosproject.net.meter.Band;
import org.onosproject.net.meter.DefaultBand;
import org.onosproject.net.meter.DefaultMeter;
import org.onosproject.net.meter.Meter;
import org.onosproject.net.meter.MeterCellId;
import org.onosproject.net.meter.MeterOperation;
import org.onosproject.net.meter.MeterProgrammable;
import org.onosproject.net.pi.model.PiMeterId;
import org.onosproject.net.pi.runtime.PiMeterCellId;

import java.util.ArrayList;
import java.util.Collection;

/**
 * Supports for updating the external gateway virtualPort.
 */
@Command(scope = "onos", name = "p4-meter",
        description = "Supports for setting the external port name.")
public class VtnCommand extends AbstractShellCommand {

    @Option(name = "-d", aliases = "--device", description = "external port name.", required = true,
            multiValued = false)
    String deviceId = "";

    @Option(name = "-p", aliases = "--port", description = "external port name.", required = true,
            multiValued = false)
    String index = "";

    @Option(name = "-r", aliases = "--rate", description = "external port name.", required = true,
            multiValued = false)
    String rate = "";

    @Option(name = "-s", aliases = "--burst", description = "external port name.", required = true,
            multiValued = false)
    String burst = "";

    @Override
    protected void execute() {

        MeterCellId ingressCellId = PiMeterCellId.ofIndirect(PiMeterId.of("port_ingress_meter"), Long.valueOf(index));
        MeterCellId ergressCellId = PiMeterCellId.ofIndirect(PiMeterId.of("port_egress_meter"), Long.valueOf(index));

        Collection<Band> bands = new ArrayList<>();
        bands.add(DefaultBand.builder().ofType(Band.Type.NONE)
                          .withRate(Long.valueOf(rate))
                          .burstSize(Long.valueOf(burst))
                          .build());
        bands.add(DefaultBand.builder().ofType(Band.Type.NONE)
                          .withRate(Long.valueOf(rate) + 10)
                          .burstSize(Long.valueOf(burst) + 10)
                          .build());
        Meter meter1 = DefaultMeter.builder()
                .withCellId(ingressCellId)
                .withBands(bands)
                .forDevice(DeviceId.deviceId(deviceId))
                .build();

        Meter meter2 = DefaultMeter.builder()
                .withCellId(ergressCellId)
                .withBands(bands)
                .forDevice(DeviceId.deviceId(deviceId))
                .build();

        ServiceDirectory serviceDirectory = new DefaultServiceDirectory();
        DeviceService deviceService = serviceDirectory.get(DeviceService.class);

        MeterProgrammable programmable;
        Device device = deviceService.getDevice(DeviceId.deviceId(deviceId));
        if (device.is(MeterProgrammable.class)) {
            programmable = device.as(MeterProgrammable.class);
        } else {
            log.error("Device {} is not meter programmable", deviceId);
            return;
        }

        try {
            Collection<Meter> meters = programmable.getMeters().get();
            log.info("The meter of device {}", meters);
        } catch (Exception e) {
            log.error("Exception occurred while get meters");
            return;
        }

        MeterOperation operation = new MeterOperation(meter1, MeterOperation.Type.MODIFY);
        try {
            Boolean isSuccess = programmable.performMeterOperation(operation).get();
            log.info("configure meter {}", isSuccess);
        } catch (Exception e) {
            log.error("Exception occurred while configure meters");
            return;
        }

        MeterOperation operation2 = new MeterOperation(meter2, MeterOperation.Type.MODIFY);
        try {
            Boolean isSuccess = programmable.performMeterOperation(operation2).get();
            log.info("configure meter {}", isSuccess);
        } catch (Exception e) {
            log.error("Exception occurred while configure meters");
            return;
        }

        try {
            Collection<Meter> meters = programmable.getMeters().get();
            log.info("The meter of device {}", meters);
        } catch (Exception e) {
            log.error("Exception occurred while get meters");
            return;
        }
    }
}
